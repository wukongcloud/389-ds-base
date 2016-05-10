# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2016 Red Hat, Inc.
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---
#
import time
import ldap
import logging
import pytest
from random import sample
from ldap.controls import SimplePagedResultsControl, GetEffectiveRightsControl
from lib389 import DirSrv, Entry, tools, tasks
from lib389.tools import DirSrvTools
from lib389._constants import *
from lib389.properties import *
from lib389.tasks import *
from lib389.utils import *
from sss_control import SSSRequestControl

logging.getLogger(__name__).setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

TEST_USER_NAME = 'simplepaged_test'
TEST_USER_DN = 'uid=%s,%s' % (TEST_USER_NAME, DEFAULT_SUFFIX)
TEST_USER_PWD = 'simplepaged_test'


class TopologyStandalone(object):
    def __init__(self, standalone):
        standalone.open()
        self.standalone = standalone


@pytest.fixture(scope="module")
def topology(request):
    # Creating standalone instance ...
    standalone = DirSrv(verbose=False)
    args_instance[SER_HOST] = HOST_STANDALONE
    args_instance[SER_PORT] = PORT_STANDALONE
    args_instance[SER_SERVERID_PROP] = SERVERID_STANDALONE
    args_instance[SER_CREATION_SUFFIX] = DEFAULT_SUFFIX
    args_standalone = args_instance.copy()
    standalone.allocate(args_standalone)
    instance_standalone = standalone.exists()
    if instance_standalone:
        standalone.delete()
    standalone.create()
    standalone.open()

    # Delete each instance in the end
    def fin():
        standalone.delete()
    request.addfinalizer(fin)

    # Clear out the tmp dir
    standalone.clearTmpDir(__file__)

    return TopologyStandalone(standalone)


@pytest.fixture(scope="module")
def test_user(topology):
    """User for binding operation"""

    try:
        topology.standalone.add_s(Entry((TEST_USER_DN, {
                                        'objectclass': 'top person'.split(),
                                        'objectclass': 'organizationalPerson',
                                        'objectclass': 'inetorgperson',
                                        'cn': TEST_USER_NAME,
                                        'sn': TEST_USER_NAME,
                                        'userpassword': TEST_USER_PWD,
                                        'mail': '%s@redhat.com' % TEST_USER_NAME,
                                        'uid': TEST_USER_NAME
                                        })))
    except ldap.LDAPError as e:
        log.error('Failed to add user (%s): error (%s)' % (TEST_USER_DN,
                                                           e.message['desc']))
        raise e


def add_users(topology, users_num):
    """Add users to the default suffix

    Return the list of added user DNs.
    """

    users_list = []
    log.info('Adding %d users' % users_num)
    for num in sample(range(1000), users_num):
        num_ran = int(round(num))
        USER_NAME = 'test%05d' % num_ran
        USER_DN = 'uid=%s,%s' % (USER_NAME, DEFAULT_SUFFIX)
        users_list.append(USER_DN)
        try:
            topology.standalone.add_s(Entry((USER_DN, {
                                             'objectclass': 'top person'.split(),
                                             'objectclass': 'organizationalPerson',
                                             'objectclass': 'inetorgperson',
                                             'cn': USER_NAME,
                                             'sn': USER_NAME,
                                             'userpassword': 'pass%s' % num_ran,
                                             'mail': '%s@redhat.com' % USER_NAME,
                                             'uid': USER_NAME})))
        except ldap.LDAPError as e:
            log.error('Failed to add user (%s): error (%s)' % (USER_DN,
                                                               e.message['desc']))
            raise e
    return users_list


def del_users(topology, users_list):
    """Delete users with DNs from given list"""

    log.info('Deleting %d users' % len(users_list))
    for user_dn in users_list:
        try:
            topology.standalone.delete_s(user_dn)
        except ldap.LDAPError as e:
            log.error('Failed to delete user (%s): error (%s)' % (user_dn,
                                                                  e.message['desc']))
            raise e


def change_conf_attr(topology, suffix, attr_name, attr_value):
    """Change configurational attribute in the given suffix.

    Returns previous attribute value.
    """

    try:
        entries = topology.standalone.search_s(suffix, ldap.SCOPE_BASE,
                                               'objectclass=top',
                                               [attr_name])
        attr_value_bck = entries[0].data.get(attr_name)
        log.info('Set %s to %s. Previous value - %s. Modified suffix - %s.' % (
                 attr_name, attr_value, attr_value_bck, suffix))
        if attr_value is None:
            topology.standalone.modify_s(suffix, [(ldap.MOD_DELETE,
                                                   attr_name,
                                                   attr_value)])
        else:
            topology.standalone.modify_s(suffix, [(ldap.MOD_REPLACE,
                                                   attr_name,
                                                   attr_value)])
    except ldap.LDAPError as e:
        log.error('Failed to change attr value (%s): error (%s)' % (attr_name,
                                                                    e.message['desc']))
        raise e

    return attr_value_bck


def paged_search(topology, controls, search_flt, searchreq_attrlist):
    """Search at the DEFAULT_SUFFIX with ldap.SCOPE_SUBTREE
    using Simple Paged Control(should the first item in the
    list controls.
    Assert that no cookie left at the end.

    Return the list with results summarized from all pages.
    """

    pages = 0
    pctrls = []
    all_results = []
    req_ctrl = controls[0]
    msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                           ldap.SCOPE_SUBTREE,
                                           search_flt,
                                           searchreq_attrlist,
                                           serverctrls=controls)
    while True:
        log.info('Getting page %d' % (pages,))
        rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)
        all_results.extend(rdata)
        pages += 1
        pctrls = [
            c
            for c in rctrls
            if c.controlType == SimplePagedResultsControl.controlType
        ]

        if pctrls:
            if pctrls[0].cookie:
                # Copy cookie from response control to request control
                req_ctrl.cookie = pctrls[0].cookie
                msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                       ldap.SCOPE_SUBTREE,
                                                       search_flt,
                                                       searchreq_attrlist,
                                                       serverctrls=controls)
            else:
                break  # No more pages available
        else:
            break

    assert not pctrls[0].cookie
    return all_results


@pytest.mark.parametrize("page_size,users_num",
                         [(6, 5), (5, 5), (5, 25)])
def test_search_success(topology, test_user, page_size, users_num):
    """Verify that search with a simple paged results control
    returns all entries it should without errors.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Search through added users with a simple paged control

    :Assert: All users should be found
    """

    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')

        all_results = paged_search(topology, [req_ctrl],
                                   search_flt, searchreq_attrlist)

        log.info('%d results' % len(all_results))
        assert len(all_results) == len(users_list)
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


@pytest.mark.parametrize("page_size,users_num,suffix,attr_name,attr_value,expected_err", [
                        (50, 200, 'cn=config,%s' % DN_LDBM, 'nsslapd-idlistscanlimit', '100',
                         ldap.UNWILLING_TO_PERFORM),
                        (5, 15, DN_CONFIG, 'nsslapd-timelimit', '20',
                         ldap.UNAVAILABLE_CRITICAL_EXTENSION),
                        (21, 50, DN_CONFIG, 'nsslapd-sizelimit', '20',
                         ldap.SIZELIMIT_EXCEEDED),
                        (21, 50, DN_CONFIG, 'nsslapd-pagedsizelimit', '5',
                         ldap.SIZELIMIT_EXCEEDED),
                        (5, 50, 'cn=config,%s' % DN_LDBM, 'nsslapd-lookthroughlimit', '20',
                         ldap.ADMINLIMIT_EXCEEDED)])
def test_search_limits_fail(topology, test_user, page_size, users_num,
                            suffix, attr_name, attr_value, expected_err):
    """Verify that search with a simple paged results control
    throws expected exceptoins when corresponding limits are
    exceeded.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Set limit attribute to the value that will cause
               an expected exception
            3. Search through added users with a simple paged control

    :Assert: Should fail with appropriate exception
    """

    users_list = add_users(topology, users_num)
    attr_value_bck = change_conf_attr(topology, suffix, attr_name, attr_value)
    conf_param_dict = {attr_name: attr_value}
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']
    controls = []

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls.append(req_ctrl)
        if attr_name == 'nsslapd-idlistscanlimit':
            sort_ctrl = SSSRequestControl(True, ['sn'])
            controls.append(sort_ctrl)
        log.info('Initiate ldapsearch with created control instance')
        msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                               ldap.SCOPE_SUBTREE,
                                               search_flt,
                                               searchreq_attrlist,
                                               serverctrls=controls)

        time_val = conf_param_dict.get('nsslapd-timelimit')
        if time_val:
            time.sleep(int(time_val) + 10)

        pages = 0
        all_results = []
        pctrls = []
        while True:
            log.info('Getting page %d' % (pages,))
            if pages == 0 and (time_val or attr_name in ('nsslapd-lookthroughlimit',
                                                         'nsslapd-pagesizelimit')):
                rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)
            else:
                with pytest.raises(expected_err):
                    rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)
                    all_results.extend(rdata)
                    pages += 1
                    pctrls = [
                        c
                        for c in rctrls
                        if c.controlType == SimplePagedResultsControl.controlType
                    ]

            if pctrls:
                if pctrls[0].cookie:
                    # Copy cookie from response control to request control
                    req_ctrl.cookie = pctrls[0].cookie
                    msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                           ldap.SCOPE_SUBTREE,
                                                           search_flt,
                                                           searchreq_attrlist,
                                                           serverctrls=controls)
                else:
                    break  # No more pages available
            else:
                break
    finally:
        if expected_err == ldap.UNAVAILABLE_CRITICAL_EXTENSION:
            topology.standalone.open()

        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)
        change_conf_attr(topology, suffix, attr_name, attr_value_bck)


def test_search_sort_success(topology, test_user):
    """Verify that search with a simple paged results control
    and a server side sort control returns all entries
    it should without errors.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Search through added users with a simple paged control
               and a server side sort control

    :Assert: All users should be found and sorted
    """

    users_num = 50
    page_size = 5
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        sort_ctrl = SSSRequestControl(True, ['sn'])

        log.info('Initiate ldapsearch with created control instance')
        log.info('Collect data with sorting')
        controls = [req_ctrl, sort_ctrl]
        results_sorted = paged_search(topology, controls,
                                      search_flt, searchreq_attrlist)

        log.info('Substring numbers from user DNs')
        r_nums = map(lambda x: int(x[0][8:13]), results_sorted)

        log.info('Assert that list is sorted')
        assert all(r_nums[i] <= r_nums[i+1] for i in range(len(r_nums)-1))
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


def test_search_abandon(topology, test_user):
    """Verify that search with simple paged results control
    can be abandon

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Search through added users with a simple paged control
            3. Abandon the search

    :Assert: It will throw an ldap.TIMEOUT exception, while trying
             to get the rest of the search results
    """

    users_num = 10
    page_size = 2
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        log.info('Initiate a search with a paged results control')
        msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                               ldap.SCOPE_SUBTREE,
                                               search_flt,
                                               searchreq_attrlist,
                                               serverctrls=controls)
        log.info('Abandon the search')
        topology.standalone.abandon(msgid)

        log.info('Expect an ldap.TIMEOUT exception, while trying to get the search results')
        with pytest.raises(ldap.TIMEOUT):
            topology.standalone.result3(msgid, timeout=5)
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


def test_search_with_timelimit(topology, test_user):
    """Verify that after performing multiple simple paged searches
    to completion, each with a timelimit, it wouldn't fail, if we sleep
    for a time more than the timelimit.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Search through added users with a simple paged control
               and timelimit set to 5
            3. When the returned cookie is empty, wait 10 seconds
            4. Perform steps 2 and 3 three times in a row

    :Assert: No error happens
    """

    users_num = 100
    page_size = 50
    timelimit = 5
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        for ii in range(3):
            log.info('Iteration %d' % ii)
            msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                   ldap.SCOPE_SUBTREE,
                                                   search_flt,
                                                   searchreq_attrlist,
                                                   serverctrls=controls,
                                                   timeout=timelimit)

            pages = 0
            pctrls = []
            while True:
                log.info('Getting page %d' % (pages,))
                rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)
                pages += 1
                pctrls = [
                    c
                    for c in rctrls
                    if c.controlType == SimplePagedResultsControl.controlType
                ]

                if pctrls:
                    if pctrls[0].cookie:
                        # Copy cookie from response control to request control
                        req_ctrl.cookie = pctrls[0].cookie
                        msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                               ldap.SCOPE_SUBTREE,
                                                               search_flt,
                                                               searchreq_attrlist,
                                                               serverctrls=controls,
                                                               timeout=timelimit)
                    else:
                        log.info('Done with this search - sleeping %d seconds' % (
                                 timelimit * 2))
                        time.sleep(timelimit * 2)
                        break  # No more pages available
                else:
                    break
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


@pytest.mark.parametrize('aci_subject',
                         ('dns = "localhost.localdomain"',
                          'ip = "::1"'))
def test_search_dns_ip_aci(topology, test_user, aci_subject):
    """Verify that after performing multiple simple paged searches
    to completion on the suffix with DNS or IP based ACI

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Back up and remove all previous ACI from suffix
            2. Add an anonymous ACI for DNS check
            3. Bind as test user
            4. Search through added users with a simple paged control
            5. Perform steps 4 three times in a row
            6. Return ACI to the initial state
            7. Go through all steps onece again, but use IP subjectdn
               insted of DNS

    :Assert: No error happens, all users should be found and sorted
    """

    users_num = 100
    page_size = 5
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Back up current suffix ACI')
        acis_bck = topology.standalone.aci.list(DEFAULT_SUFFIX, ldap.SCOPE_BASE)

        log.info('Add test ACI')
        ACI_TARGET = '(targetattr != "userPassword")'
        ACI_ALLOW = '(version 3.0;acl "Anonymous access within domain"; allow (read,compare,search)'
        ACI_SUBJECT = '(userdn = "ldap:///anyone") and (%s);)' % aci_subject
        ACI_BODY = ACI_TARGET + ACI_ALLOW + ACI_SUBJECT
        try:
            topology.standalone.modify_s(DEFAULT_SUFFIX, [(ldap.MOD_REPLACE,
                                                           'aci',
                                                           ACI_BODY)])
        except ldap.LDAPError as e:
            log.fatal('Failed to add ACI: error (%s)' % (e.message['desc']))
            raise e

        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        log.info('Initiate three searches with a paged results control')
        for ii in range(3):
            log.info('%d search' % (ii + 1))
            all_results = paged_search(topology, controls,
                                       search_flt, searchreq_attrlist)
            log.info('%d results' % len(all_results))
            assert len(all_results) == len(users_list)
        log.info('If we are here, then no error has happened. We are good.')

    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        log.info('Restore ACI')
        topology.standalone.modify_s(DEFAULT_SUFFIX, [(ldap.MOD_DELETE,
                                                       'aci',
                                                       None)])
        for aci in acis_bck:
            topology.standalone.modify_s(DEFAULT_SUFFIX, [(ldap.MOD_ADD,
                                                           'aci',
                                                           aci.getRawAci())])
        del_users(topology, users_list)


def test_search_multiple_paging(topology, test_user):
    """Verify that after performing multiple simple paged searches
    on a single connection without a complition, it wouldn't fail.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Initiate the search with a simple paged control
            3. Acquire the returned cookie only one time
            4. Perform steps 2 and 3 three times in a row

    :Assert: No error happens
    """

    users_num = 100
    page_size = 30
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        for ii in range(3):
            log.info('Iteration %d' % ii)
            msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                   ldap.SCOPE_SUBTREE,
                                                   search_flt,
                                                   searchreq_attrlist,
                                                   serverctrls=controls)
            rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)
            pctrls = [
                c
                for c in rctrls
                if c.controlType == SimplePagedResultsControl.controlType
            ]

            # Copy cookie from response control to request control
            req_ctrl.cookie = pctrls[0].cookie
            msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                   ldap.SCOPE_SUBTREE,
                                                   search_flt,
                                                   searchreq_attrlist,
                                                   serverctrls=controls)
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


@pytest.mark.parametrize("invalid_cookie", [1000, -1])
def test_search_invalid_cookie(topology, test_user, invalid_cookie):
    """Verify that using invalid cookie while performing
    search with the simple paged results control throws
    a TypeError exception

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Initiate the search with a simple paged control
            3. Put an invalid cookie (-1, 1000) to the control
            4. Continue the search

    :Assert: It will throw an TypeError exception
    """

    users_num = 100
    page_size = 50
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                               ldap.SCOPE_SUBTREE,
                                               search_flt,
                                               searchreq_attrlist,
                                               serverctrls=controls)
        rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)

        log.info('Put an invalid cookie (%d) to the control. TypeError is expected' %
                 invalid_cookie)
        req_ctrl.cookie = invalid_cookie
        with pytest.raises(TypeError):
            msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                                   ldap.SCOPE_SUBTREE,
                                                   search_flt,
                                                   searchreq_attrlist,
                                                   serverctrls=controls)
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


def test_search_abandon_with_zero_size(topology, test_user):
    """Verify that search with simple paged results control
    can be abandon using page_size = 0

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Bind as test user
            2. Search through added users with a simple paged control
               and page_size = 0

    :Assert: No cookie should be returned at all
    """

    users_num = 10
    page_size = 0
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        msgid = topology.standalone.search_ext(DEFAULT_SUFFIX,
                                               ldap.SCOPE_SUBTREE,
                                               search_flt,
                                               searchreq_attrlist,
                                               serverctrls=controls)
        rtype, rdata, rmsgid, rctrls = topology.standalone.result3(msgid)
        pctrls = [
            c
            for c in rctrls
            if c.controlType == SimplePagedResultsControl.controlType
        ]
        assert not pctrls[0].cookie
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)


def test_search_pagedsizelimit_success(topology, test_user):
    """Verify that search with a simple paged results control
    returns all entries it should without errors while
    valid value set to nsslapd-pagedsizelimit.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            10 users for the search base

    :Steps: 1. Set nsslapd-pagedsizelimit: 20
            2. Bind as test user
            3. Search through added users with a simple paged control
               using page_size = 10

    :Assert: All users should be found
    """

    users_num = 10
    page_size = 10
    attr_name = 'nsslapd-pagedsizelimit'
    attr_value = '20'
    attr_value_bck = change_conf_attr(topology, DN_CONFIG,
                                      attr_name, attr_value)
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        all_results = paged_search(topology, controls,
                                   search_flt, searchreq_attrlist)

        log.info('%d results' % len(all_results))
        assert len(all_results) == len(users_list)

    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)
        change_conf_attr(topology, DN_CONFIG,
                         'nsslapd-pagedsizelimit', attr_value_bck)


@pytest.mark.parametrize('conf_attr,user_attr,expected_rs',
                         (('5', '15', 'PASS'), ('15', '5', ldap.SIZELIMIT_EXCEEDED)))
def test_search_nspagedsizelimit(topology, test_user,
                                 conf_attr, user_attr, expected_rs):
    """Verify that nsPagedSizeLimit attribute overrides
    nsslapd-pagedsizelimit while performing search with
    the simple paged results control.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            10 users for the search base

    :Steps: 1. Set nsslapd-pagedsizelimit: 5
            2. Set nsPagedSizeLimit: 15
            3. Bind as test user
            4. Search through added users with a simple paged control
               using page_size = 10
            5. Bind as Directory Manager
            6. Restore all values
            7. Set nsslapd-pagedsizelimit: 15
            8. Set nsPagedSizeLimit: 5
            9. Bind as test user
            10. Search through added users with a simple paged control
                using page_size = 10

    :Assert: After the steps 1-4, it should PASS.
             After the steps 7-10, it should throw
             SIZELIMIT_EXCEEDED exception
    """

    users_num = 10
    page_size = 10
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']
    conf_attr_bck = change_conf_attr(topology, DN_CONFIG,
                                     'nsslapd-pagedsizelimit', conf_attr)
    user_attr_bck = change_conf_attr(topology, TEST_USER_DN,
                                     'nsPagedSizeLimit', user_attr)

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        if expected_rs == ldap.SIZELIMIT_EXCEEDED:
            log.info('Expect to fail with SIZELIMIT_EXCEEDED')
            with pytest.raises(expected_rs):
                all_results = paged_search(topology, controls,
                                           search_flt, searchreq_attrlist)
        elif expected_rs == 'PASS':
            log.info('Expect to pass')
            all_results = paged_search(topology, controls,
                                       search_flt, searchreq_attrlist)
            log.info('%d results' % len(all_results))
            assert len(all_results) == len(users_list)

    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)
        change_conf_attr(topology, DN_CONFIG,
                         'nsslapd-pagedsizelimit', conf_attr_bck)
        change_conf_attr(topology, TEST_USER_DN,
                         'nsPagedSizeLimit', user_attr_bck)


@pytest.mark.parametrize('conf_attr_values,expected_rs',
                         ((('5000', '100', '100'), ldap.ADMINLIMIT_EXCEEDED),
                          (('5000', '120', '122'), 'PASS')))
def test_search_paged_limits(topology, test_user, conf_attr_values, expected_rs):
    """Verify that nsslapd-idlistscanlimit and
    nsslapd-lookthroughlimit can limit the administrator
    search abilities.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            10 users for the search base

    :Steps: 1. Set nsslapd-sizelimit and nsslapd-pagedsizelimit to 5000
            2. Set nsslapd-idlistscanlimit: 120
            3. Set nsslapd-lookthroughlimit: 122
            4. Bind as test user
            5. Search through added users with a simple paged control
               using page_size = 10
            6. Bind as Directory Manager
            7. Set nsslapd-idlistscanlimit: 100
            8. Set nsslapd-lookthroughlimit: 100
            9. Bind as test user
            10. Search through added users with a simple paged control
                using page_size = 10

    :Assert: After the steps 1-4, it should PASS.
             After the steps 7-10, it should throw
             ADMINLIMIT_EXCEEDED exception
    """

    users_num = 101
    page_size = 10
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']
    size_attr_bck = change_conf_attr(topology, DN_CONFIG,
                                     'nsslapd-sizelimit', conf_attr_values[0])
    pagedsize_attr_bck = change_conf_attr(topology, DN_CONFIG,
                                          'nsslapd-pagedsizelimit', conf_attr_values[0])
    idlistscan_attr_bck = change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                                           'nsslapd-idlistscanlimit', conf_attr_values[1])
    lookthrough_attr_bck = change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                                            'nsslapd-lookthroughlimit', conf_attr_values[2])

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        if expected_rs == ldap.ADMINLIMIT_EXCEEDED:
            log.info('Expect to fail with ADMINLIMIT_EXCEEDED')
            with pytest.raises(expected_rs):
                all_results = paged_search(topology, controls,
                                           search_flt, searchreq_attrlist)
        elif expected_rs == 'PASS':
            log.info('Expect to pass')
            all_results = paged_search(topology, controls,
                                       search_flt, searchreq_attrlist)
            log.info('%d results' % len(all_results))
            assert len(all_results) == len(users_list)
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)
        change_conf_attr(topology, DN_CONFIG,
                         'nsslapd-sizelimit', size_attr_bck)
        change_conf_attr(topology, DN_CONFIG,
                         'nsslapd-pagedsizelimit', pagedsize_attr_bck)
        change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                         'nsslapd-lookthroughlimit', lookthrough_attr_bck)
        change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                         'nsslapd-idlistscanlimit', idlistscan_attr_bck)


@pytest.mark.parametrize('conf_attr_values,expected_rs',
                         ((('1000', '100', '100'), ldap.ADMINLIMIT_EXCEEDED),
                          (('1000', '120', '122'), 'PASS')))
def test_search_paged_user_limits(topology, test_user, conf_attr_values, expected_rs):
    """Verify that nsPagedIDListScanLimit and nsPagedLookthroughLimit
    override nsslapd-idlistscanlimit and nsslapd-lookthroughlimit
    while performing search with the simple paged results control.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            10 users for the search base

    :Steps: 1. Set nsslapd-idlistscanlimit: 1000
            2. Set nsslapd-lookthroughlimit: 1000
            3. Set nsPagedIDListScanLimit: 120
            4. Set nsPagedLookthroughLimit: 122
            5. Bind as test user
            6. Search through added users with a simple paged control
               using page_size = 10
            7. Bind as Directory Manager
            8. Set nsPagedIDListScanLimit: 100
            9. Set nsPagedLookthroughLimit: 100
            10. Bind as test user
            11. Search through added users with a simple paged control
                using page_size = 10

    :Assert: After the steps 1-4, it should PASS.
             After the steps 8-11, it should throw
             ADMINLIMIT_EXCEEDED exception
    """

    users_num = 101
    page_size = 10
    users_list = add_users(topology, users_num)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']
    lookthrough_attr_bck = change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                                            'nsslapd-lookthroughlimit', conf_attr_values[0])
    idlistscan_attr_bck = change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                                           'nsslapd-idlistscanlimit', conf_attr_values[0])
    user_idlistscan_attr_bck = change_conf_attr(topology, TEST_USER_DN,
                                                'nsPagedIDListScanLimit', conf_attr_values[1])
    user_lookthrough_attr_bck = change_conf_attr(topology, TEST_USER_DN,
                                                 'nsPagedLookthroughLimit', conf_attr_values[2])

    try:
        log.info('Set user bind')
        topology.standalone.simple_bind_s(TEST_USER_DN, TEST_USER_PWD)

        log.info('Create simple paged results control instance')
        req_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        controls = [req_ctrl]

        if expected_rs == ldap.ADMINLIMIT_EXCEEDED:
            log.info('Expect to fail with ADMINLIMIT_EXCEEDED')
            with pytest.raises(expected_rs):
                all_results = paged_search(topology, controls,
                                           search_flt, searchreq_attrlist)
        elif expected_rs == 'PASS':
            log.info('Expect to pass')
            all_results = paged_search(topology, controls,
                                       search_flt, searchreq_attrlist)
            log.info('%d results' % len(all_results))
            assert len(all_results) == len(users_list)
    finally:
        log.info('Set Directory Manager bind back')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)
        del_users(topology, users_list)
        change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                         'nsslapd-lookthroughlimit', lookthrough_attr_bck)
        change_conf_attr(topology, 'cn=config,%s' % DN_LDBM,
                         'nsslapd-idlistscanlimit', idlistscan_attr_bck)
        change_conf_attr(topology, TEST_USER_DN,
                         'nsPagedIDListScanLimit', user_idlistscan_attr_bck)
        change_conf_attr(topology, TEST_USER_DN,
                         'nsPagedLookthroughLimit', user_lookthrough_attr_bck)


def test_ger_basic(topology, test_user):
    """Verify that search with a simple paged results control
    and get effective rights control returns all entries
    it should without errors.

    :Feature: Simple paged results

    :Setup: Standalone instance, test user for binding,
            variated number of users for the search base

    :Steps: 1. Search through added users with a simple paged control
               and get effective rights control

    :Assert: All users should be found, every found entry should have
             an 'attributeLevelRights' returned
    """

    users_list = add_users(topology, 20)
    search_flt = r'(uid=test*)'
    searchreq_attrlist = ['dn', 'sn']
    page_size = 4

    try:
        log.info('Set bind to directory manager')
        topology.standalone.simple_bind_s(DN_DM, PASSWORD)

        log.info('Create simple paged results control instance')
        spr_ctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
        ger_ctrl = GetEffectiveRightsControl(True, "dn: " + DN_DM)

        all_results = paged_search(topology, [spr_ctrl, ger_ctrl],
                                   search_flt, searchreq_attrlist)

        log.info('{} results'.format(len(all_results)))
        assert len(all_results) == len(users_list)
        log.info('Check for attributeLevelRights')
        assert all(attrs['attributeLevelRights'][0] for dn, attrs in all_results)
    finally:
        log.info('Remove added users')
        del_users(topology, users_list)


if __name__ == '__main__':
    # Run isolated
    # -s for DEBUG mode
    CURRENT_FILE = os.path.realpath(__file__)
    pytest.main("-s %s" % CURRENT_FILE)
