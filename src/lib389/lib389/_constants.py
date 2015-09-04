# replicatype @see https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Directory_Server/8.1/html/Administration_Guide/Managing_Replication-Configuring-Replication-cmd.html
# 2 for consumers and hubs (read-only replicas)
# 3 for both single and multi-master suppliers (read-write replicas)

import os
from lib389.properties import *

(MASTER_TYPE,
 HUB_TYPE,
 LEAF_TYPE) = list(range(3))

REPLICAROLE_MASTER    = "master"
REPLICAROLE_HUB       = "hub"
REPLICAROLE_CONSUMER  = "consumer"

CONSUMER_REPLICAID = 65535

REPLICA_RDONLY_TYPE = 2  # CONSUMER and HUB
REPLICA_WRONLY_TYPE = 1  # SINGLE and MULTI MASTER
REPLICA_RDWR_TYPE   = REPLICA_RDONLY_TYPE | REPLICA_WRONLY_TYPE

REPLICA_RUV_UUID        = "ffffffff-ffffffff-ffffffff-ffffffff"
REPLICA_RUV_FILTER      = '(&(nsuniqueid=ffffffff-ffffffff-ffffffff-ffffffff)(objectclass=nstombstone))'
REPLICA_OC_TOMBSTONE    = "nsTombstone"
REPLICATION_BIND_DN     = 'replication_bind_dn'
REPLICATION_BIND_PW     = 'replication_bind_pw'
REPLICATION_BIND_METHOD = 'replication_bind_method'
REPLICATION_TRANSPORT   = 'replication_transport'
REPLICATION_TIMEOUT     = 'replication_timeout'

TRANS_STARTTLS  = "starttls"
TRANS_SECURE    = "secure"
TRANS_NORMAL    = "normal"
REPL_TRANS_VALUE = {TRANS_STARTTLS: 'TLS',
                    TRANS_SECURE:   'SSL',
                    TRANS_NORMAL:   'LDAP'}

defaultProperties = {
    REPLICATION_BIND_DN:        "cn=replrepl,cn=config",
    REPLICATION_BIND_PW:        "password",
    REPLICATION_BIND_METHOD:    "simple",
    REPLICATION_TRANSPORT:      REPL_TRANS_VALUE[TRANS_NORMAL],
    REPLICATION_TIMEOUT:        str(120)
}


CFGSUFFIX = "o=NetscapeRoot"

# Some DN constants
DN_DM = "cn=Directory Manager"
PW_DM = "password"
DN_CONFIG = "cn=config"
DN_LDBM = "cn=ldbm database,cn=plugins,cn=config"
DN_SCHEMA = "cn=schema"

CMD_PATH_SETUP_DS = "/setup-ds.pl"
CMD_PATH_REMOVE_DS = "/remove-ds.pl"

# State of an DirSrv object
DIRSRV_STATE_INIT = 'initial'
DIRSRV_STATE_ALLOCATED = 'allocated'
DIRSRV_STATE_OFFLINE = 'offline'
DIRSRV_STATE_ONLINE = 'online'

LOCALHOST = "localhost.localdomain"
DEFAULT_PORT        = 389
DEFAULT_SECURE_PORT = 636
DEFAULT_SUFFIX      = 'dc=example,dc=com'
DEFAULT_BENAME      = 'userRoot'    # warning it is case sensitive
DEFAULT_BACKUPDIR   = '/tmp'
DEFAULT_INST_HEAD   = 'slapd-'
DEFAULT_ENV_HEAD    = 'dirsrv-'
DEFAULT_CHANGELOG_NAME = "changelog5"
DEFAULT_CHANGELOG_DB   = 'changelogdb'

CONF_DIR = 'etc/dirsrv'
ENV_SYSCONFIG_DIR = '/etc/sysconfig'
ENV_LOCAL_DIR = '.dirsrv'

# CONFIG file (<prefix>/etc/sysconfig/dirsrv-* or $HOME/.dirsrv/dirsrv-*) keywords
CONF_SERVER_ID     = 'SERVER_ID'
CONF_SERVER_DIR    = 'SERVER_DIR'
CONF_SERVERBIN_DIR = 'SERVERBIN_DIR'
CONF_CONFIG_DIR    = 'CONFIG_DIR'
CONF_INST_DIR      = 'INST_DIR'
CONF_RUN_DIR       = 'RUN_DIR'
CONF_DS_ROOT       = 'DS_ROOT'
CONF_PRODUCT_NAME  = 'PRODUCT_NAME'

DN_CONFIG       = "cn=config"
DN_PLUGIN       = "cn=plugins,%s"       % DN_CONFIG
DN_MAPPING_TREE = "cn=mapping tree,%s"  % DN_CONFIG
DN_CHANGELOG    = "cn=changelog5,%s"    % DN_CONFIG
DN_LDBM         = "cn=ldbm database,%s" % DN_PLUGIN
DN_CHAIN        = "cn=chaining database,%s" % DN_PLUGIN

DN_TASKS           = "cn=tasks,%s"            % DN_CONFIG
DN_INDEX_TASK      = "cn=index,%s"            % DN_TASKS
DN_EXPORT_TASK     = "cn=export,%s"           % DN_TASKS
DN_IMPORT_TASK     = "cn=import,%s"           % DN_TASKS
DN_BACKUP_TASK     = "cn=backup,%s"           % DN_TASKS
DN_RESTORE_TASK    = "cn=restore,%s"          % DN_TASKS
DN_MBO_TASK        = "cn=memberOf task,%s"    % DN_TASKS
DN_TOMB_FIXUP_TASK = "cn=fixup tombstones,%s" % DN_TASKS

# Script Constants
LDIF2DB =  '/ldif2db'
DB2LDIF =  '/db2ldif'
BAK2DB =   '/bak2db'
DB2BAK =   '/db2bak'
DB2INDEX = '/db2index'
DBSCAN = '/dbscan'

RDN_REPLICA     = "cn=replica"

RETROCL_SUFFIX = "cn=changelog"

##################################
###
### Request Control OIDS
###
##################################
CONTROL_DEREF = '1.3.6.1.4.1.4203.666.5.16'

##################################
###
### Plugins
###
##################################

PLUGIN_7_BIT_CHECK        = '7-bit check'
PLUGIN_ACCT_POLICY        = 'Account Policy Plugin'
PLUGIN_ACCT_USABILITY     = 'Account Usability Plugin'
PLUGIN_ACL                = 'ACL Plugin'
PLUGIN_ACL_PREOP          = 'ACL preoperation'
PLUGIN_ATTR_UNIQUENESS    = 'attribute uniqueness'
PLUGIN_AUTOMEMBER         = 'Auto Membership Plugin'
PLUGIN_CHAININGDB         = 'chaining database'
PLUGIN_COLLATION          = 'Internationalization Plugin'
PLUGIN_COS                = 'Class of Service'
PLUGIN_DEREF              = 'deref'
PLUGIN_DNA                = 'Distributed Numeric Assignment Plugin'
PLUGIN_HTTP               = 'HTTP Client'
PLUGIN_LINKED_ATTRS       = 'Linked Attributes'
PLUGIN_MANAGED_ENTRY      = 'Managed Entries'
PLUGIN_MEMBER_OF          = 'MemberOf Plugin'
PLUGIN_PAM_PASSTHRU       = 'PAM Pass Through Auth'
PLUGIN_PASSTHRU           = 'Pass Through Authentication'
PLUGIN_POSIX_WINSYNC      = 'Posix Winsync API'
PLUGIN_REFER_INTEGRITY    = 'referential integrity postoperation'
PLUGIN_REPL_SYNC          = 'Content Synchronization'
PLUGIN_REPLICATION_LEGACY = 'Legacy Replication Plugin'
PLUGIN_REPLICATION        = 'Multimaster Replication Plugin'
PLUGIN_RETRO_CHANGELOG    = 'Retro Changelog Plugin'
PLUGIN_ROLES              = 'Roles Plugin'
PLUGIN_ROOTDN_ACCESS      = 'RootDN Access Control'
PLUGIN_SCHEMA_RELOAD      = 'Schema Reload'
PLUGIN_STATECHANGE        = 'State Change Plugin'
PLUGIN_USN                = 'USN'
PLUGIN_VIEWS              = 'Views'
PLUGIN_WHOAMI             = 'whoami'


#
# Constants
#
DEFAULT_USER = "dirsrv"
DEFAULT_USERHOME = "/tmp/lib389_home"
DEFAULT_USER_COMMENT = "lib389 DS user"
DATA_DIR = "data"
TMP_DIR = "tmp"
VALGRIND_WRAPPER = "ns-slapd.valgrind"
VALGRIND_LEAK_STR = " blocks are definitely lost in loss record "
VALGRIND_INVALID_STR = " Invalid (free|read|write)"
DISORDERLY_SHUTDOWN = 'Detected Disorderly Shutdown last time Directory Server was running, recovering database'

#
# LOG: see https://access.redhat.com/documentation/en-US/Red_Hat_Directory_Server/10/html/Administration_Guide/Configuring_Logs.html
# The default log level is 16384
#
(
LOG_TRACE,
LOG_TRACE_PACKETS,
LOG_TRACE_HEAVY,
LOG_CONNECT,
LOG_PACKET,
LOG_SEARCH_FILTER,
LOG_CONFIG_PARSER,
LOG_ACL,
LOG_ENTRY_PARSER,
LOG_HOUSEKEEPING,
LOG_REPLICA,
LOG_DEFAULT,
LOG_CACHE,
LOG_PLUGIN,
LOG_MICROSECONDS,
LOG_ACL_SUMMARY) = [1 << x for x in (list(range(8)) + list(range(11, 19)))]


#
# Constants for individual tests
#
SUFFIX = 'dc=example,dc=com'
PASSWORD = 'password'

# Standalone topology - 10 instances
HOST_STANDALONE = LOCALHOST
PORT_STANDALONE = 31389
SERVERID_STANDALONE = 'standalone'

HOST_STANDALONE2 = LOCALHOST
PORT_STANDALONE2 = 32389
SERVERID_STANDALONE2 = 'standalone_2'

HOST_STANDALONE3 = LOCALHOST
PORT_STANDALONE3 = 33389
SERVERID_STANDALONE3 = 'standalone_3'

HOST_STANDALONE4 = LOCALHOST
PORT_STANDALONE4 = 34389
SERVERID_STANDALONE4 = 'standalone_4'

HOST_STANDALONE5 = LOCALHOST
PORT_STANDALONE5 = 35389
SERVERID_STANDALONE5 = 'standalone_5'

HOST_STANDALONE6 = LOCALHOST
PORT_STANDALONE6 = 36389
SERVERID_STANDALONE6 = 'standalone_6'

HOST_STANDALONE7 = LOCALHOST
PORT_STANDALONE7 = 37389
SERVERID_STANDALONE7 = 'standalone_7'

HOST_STANDALONE8 = LOCALHOST
PORT_STANDALONE8 = 38389
SERVERID_STANDALONE8 = 'standalone_8'

HOST_STANDALONE9 = LOCALHOST
PORT_STANDALONE9 = 39389
SERVERID_STANDALONE9 = 'standalone_9'

HOST_STANDALONE10 = LOCALHOST
PORT_STANDALONE10 = 30389
SERVERID_STANDALONE10 = 'standalone_10'

# Replication topology: 10 masters, 10 hubs, 10 consumers
HOST_MASTER_1 = LOCALHOST
PORT_MASTER_1 = 41389
SERVERID_MASTER_1 = 'master_1'
REPLICAID_MASTER_1 = 1

HOST_MASTER_2 = LOCALHOST
PORT_MASTER_2 = 42389
SERVERID_MASTER_2 = 'master_2'
REPLICAID_MASTER_2 = 2

HOST_MASTER_3 = LOCALHOST
PORT_MASTER_3 = 43389
SERVERID_MASTER_3 = 'master_3'
REPLICAID_MASTER_3 = 3

HOST_MASTER_4 = LOCALHOST
PORT_MASTER_4 = 44389
SERVERID_MASTER_4 = 'master_4'
REPLICAID_MASTER_4 = 4

HOST_MASTER_5 = LOCALHOST
PORT_MASTER_5 = 45389
SERVERID_MASTER_5 = 'master_5'
REPLICAID_MASTER_5 = 5

HOST_MASTER_6 = LOCALHOST
PORT_MASTER_6 = 46389
SERVERID_MASTER_6 = 'master_6'
REPLICAID_MASTER_6 = 6

HOST_MASTER_7 = LOCALHOST
PORT_MASTER_7 = 47389
SERVERID_MASTER_7 = 'master_7'
REPLICAID_MASTER_7 = 7

HOST_MASTER_8 = LOCALHOST
PORT_MASTER_8 = 48389
SERVERID_MASTER_8 = 'master_8'
REPLICAID_MASTER_8 = 8

HOST_MASTER_9 = LOCALHOST
PORT_MASTER_9 = 49389
SERVERID_MASTER_9 = 'master_9'
REPLICAID_MASTER_9 = 9

HOST_MASTER_10 = LOCALHOST
PORT_MASTER_10 = 40389
SERVERID_MASTER_10 = 'master_10'
REPLICAID_MASTER_10 = 10

HOST_HUB_1 = LOCALHOST
PORT_HUB_1 = 51389
SERVERID_HUB_1 = 'hub_1'
REPLICAID_HUB_1 = 65535

HOST_HUB_2 = LOCALHOST
PORT_HUB_2 = 52389
SERVERID_HUB_2 = 'hub_2'
REPLICAID_HUB_2 = 65535

HOST_HUB_3 = LOCALHOST
PORT_HUB_3 = 53389
SERVERID_HUB_3 = 'hub_3'
REPLICAID_HUB_3 = 65535

HOST_HUB_4 = LOCALHOST
PORT_HUB_4 = 54389
SERVERID_HUB_4 = 'hub_4'
REPLICAID_HUB_4 = 65535

HOST_HUB_5 = LOCALHOST
PORT_HUB_5 = 55389
SERVERID_HUB_5 = 'hub_5'
REPLICAID_HUB_5 = 65535

HOST_HUB_6 = LOCALHOST
PORT_HUB_6 = 56389
SERVERID_HUB_6 = 'hub_6'
REPLICAID_HUB_6 = 65535

HOST_HUB_7 = LOCALHOST
PORT_HUB_7 = 57389
SERVERID_HUB_7 = 'hub_7'
REPLICAID_HUB_7 = 65535

HOST_HUB_8 = LOCALHOST
PORT_HUB_8 = 58389
SERVERID_HUB_8 = 'hub_8'
REPLICAID_HUB_8 = 65535

HOST_HUB_9 = LOCALHOST
PORT_HUB_9 = 59389
SERVERID_HUB_9 = 'hub_9'
REPLICAID_HUB_9 = 65535

HOST_HUB_10 = LOCALHOST
PORT_HUB_10 = 50389
SERVERID_HUB_10 = 'hub_10'
REPLICAID_HUB_10 = 65535

HOST_CONSUMER_1 = LOCALHOST
PORT_CONSUMER_1 = 61389
SERVERID_CONSUMER_1 = 'consumer_1'

HOST_CONSUMER_2 = LOCALHOST
PORT_CONSUMER_2 = 62389
SERVERID_CONSUMER_2 = 'consumer_2'

HOST_CONSUMER_3 = LOCALHOST
PORT_CONSUMER_3 = 63389
SERVERID_CONSUMER_3 = 'consumer_3'

HOST_CONSUMER_4 = LOCALHOST
PORT_CONSUMER_4 = 64389
SERVERID_CONSUMER_4 = 'consumer_4'

HOST_CONSUMER_5 = LOCALHOST
PORT_CONSUMER_5 = 65389
SERVERID_CONSUMER_5 = 'consumer_5'

HOST_CONSUMER_6 = LOCALHOST
PORT_CONSUMER_6 = 66389
SERVERID_CONSUMER_6 = 'consumer_6'

HOST_CONSUMER_7 = LOCALHOST
PORT_CONSUMER_7 = 67389
SERVERID_CONSUMER_7 = 'consumer_7'

HOST_CONSUMER_8 = LOCALHOST
PORT_CONSUMER_8 = 68389
SERVERID_CONSUMER_8 = 'consumer_8'

HOST_CONSUMER_9 = LOCALHOST
PORT_CONSUMER_9 = 69389
SERVERID_CONSUMER_9 = 'consumer_9'

HOST_CONSUMER_10 = LOCALHOST
PORT_CONSUMER_10 = 60389
SERVERID_CONSUMER_10 = 'consumer_10'

# Each defined instance above must be added in that list
ALL_INSTANCES = [{SER_HOST: HOST_STANDALONE, SER_PORT: PORT_STANDALONE, SER_SERVERID_PROP: SERVERID_STANDALONE},
                 {SER_HOST: HOST_STANDALONE2, SER_PORT: PORT_STANDALONE2, SER_SERVERID_PROP: SERVERID_STANDALONE2},
                 {SER_HOST: HOST_STANDALONE3, SER_PORT: PORT_STANDALONE3, SER_SERVERID_PROP: SERVERID_STANDALONE3},
                 {SER_HOST: HOST_STANDALONE4, SER_PORT: PORT_STANDALONE4, SER_SERVERID_PROP: SERVERID_STANDALONE4},
                 {SER_HOST: HOST_STANDALONE5, SER_PORT: PORT_STANDALONE5, SER_SERVERID_PROP: SERVERID_STANDALONE5},
                 {SER_HOST: HOST_STANDALONE6, SER_PORT: PORT_STANDALONE6, SER_SERVERID_PROP: SERVERID_STANDALONE6},
                 {SER_HOST: HOST_STANDALONE7, SER_PORT: PORT_STANDALONE7, SER_SERVERID_PROP: SERVERID_STANDALONE7},
                 {SER_HOST: HOST_STANDALONE8, SER_PORT: PORT_STANDALONE8, SER_SERVERID_PROP: SERVERID_STANDALONE8},
                 {SER_HOST: HOST_STANDALONE9, SER_PORT: PORT_STANDALONE9, SER_SERVERID_PROP: SERVERID_STANDALONE9},
                 {SER_HOST: HOST_STANDALONE10, SER_PORT: PORT_STANDALONE10, SER_SERVERID_PROP: SERVERID_STANDALONE10},
                 {SER_HOST: HOST_MASTER_1, SER_PORT: PORT_MASTER_1, SER_SERVERID_PROP: SERVERID_MASTER_1},
                 {SER_HOST: HOST_MASTER_2, SER_PORT: PORT_MASTER_2, SER_SERVERID_PROP: SERVERID_MASTER_2},
                 {SER_HOST: HOST_MASTER_3, SER_PORT: PORT_MASTER_3, SER_SERVERID_PROP: SERVERID_MASTER_3},
                 {SER_HOST: HOST_MASTER_4, SER_PORT: PORT_MASTER_4, SER_SERVERID_PROP: SERVERID_MASTER_4},
                 {SER_HOST: HOST_MASTER_5, SER_PORT: PORT_MASTER_5, SER_SERVERID_PROP: SERVERID_MASTER_5},
                 {SER_HOST: HOST_MASTER_6, SER_PORT: PORT_MASTER_6, SER_SERVERID_PROP: SERVERID_MASTER_6},
                 {SER_HOST: HOST_MASTER_7, SER_PORT: PORT_MASTER_7, SER_SERVERID_PROP: SERVERID_MASTER_7},
                 {SER_HOST: HOST_MASTER_8, SER_PORT: PORT_MASTER_8, SER_SERVERID_PROP: SERVERID_MASTER_8},
                 {SER_HOST: HOST_MASTER_9, SER_PORT: PORT_MASTER_9, SER_SERVERID_PROP: SERVERID_MASTER_9},
                 {SER_HOST: HOST_MASTER_10, SER_PORT: PORT_MASTER_10, SER_SERVERID_PROP: SERVERID_MASTER_10},
                 {SER_HOST: HOST_HUB_1, SER_PORT: PORT_HUB_1, SER_SERVERID_PROP: SERVERID_HUB_1},
                 {SER_HOST: HOST_HUB_2, SER_PORT: PORT_HUB_2, SER_SERVERID_PROP: SERVERID_HUB_2},
                 {SER_HOST: HOST_HUB_3, SER_PORT: PORT_HUB_3, SER_SERVERID_PROP: SERVERID_HUB_3},
                 {SER_HOST: HOST_HUB_4, SER_PORT: PORT_HUB_4, SER_SERVERID_PROP: SERVERID_HUB_4},
                 {SER_HOST: HOST_HUB_5, SER_PORT: PORT_HUB_5, SER_SERVERID_PROP: SERVERID_HUB_5},
                 {SER_HOST: HOST_HUB_6, SER_PORT: PORT_HUB_6, SER_SERVERID_PROP: SERVERID_HUB_6},
                 {SER_HOST: HOST_HUB_7, SER_PORT: PORT_HUB_7, SER_SERVERID_PROP: SERVERID_HUB_7},
                 {SER_HOST: HOST_HUB_8, SER_PORT: PORT_HUB_8, SER_SERVERID_PROP: SERVERID_HUB_8},
                 {SER_HOST: HOST_HUB_9, SER_PORT: PORT_HUB_9, SER_SERVERID_PROP: SERVERID_HUB_9},
                 {SER_HOST: HOST_HUB_10, SER_PORT: PORT_HUB_10, SER_SERVERID_PROP: SERVERID_HUB_10},
                 {SER_HOST: HOST_CONSUMER_1, SER_PORT: PORT_CONSUMER_1, SER_SERVERID_PROP: SERVERID_CONSUMER_1},
                 {SER_HOST: HOST_CONSUMER_2, SER_PORT: PORT_CONSUMER_2, SER_SERVERID_PROP: SERVERID_CONSUMER_2},
                 {SER_HOST: HOST_CONSUMER_3, SER_PORT: PORT_CONSUMER_3, SER_SERVERID_PROP: SERVERID_CONSUMER_3},
                 {SER_HOST: HOST_CONSUMER_4, SER_PORT: PORT_CONSUMER_4, SER_SERVERID_PROP: SERVERID_CONSUMER_4},
                 {SER_HOST: HOST_CONSUMER_5, SER_PORT: PORT_CONSUMER_5, SER_SERVERID_PROP: SERVERID_CONSUMER_5},
                 {SER_HOST: HOST_CONSUMER_6, SER_PORT: PORT_CONSUMER_6, SER_SERVERID_PROP: SERVERID_CONSUMER_6},
                 {SER_HOST: HOST_CONSUMER_7, SER_PORT: PORT_CONSUMER_7, SER_SERVERID_PROP: SERVERID_CONSUMER_7},
                 {SER_HOST: HOST_CONSUMER_8, SER_PORT: PORT_CONSUMER_8, SER_SERVERID_PROP: SERVERID_CONSUMER_8},
                 {SER_HOST: HOST_CONSUMER_9, SER_PORT: PORT_CONSUMER_9, SER_SERVERID_PROP: SERVERID_CONSUMER_9},
                 {SER_HOST: HOST_CONSUMER_10, SER_PORT: PORT_CONSUMER_10, SER_SERVERID_PROP: SERVERID_CONSUMER_10},
                ]

# This is a template
args_instance = {
                   SER_DEPLOYED_DIR: os.environ.get('PREFIX', None),
                   SER_BACKUP_INST_DIR: os.environ.get('BACKUPDIR', DEFAULT_BACKUPDIR),
                   SER_ROOT_DN: DN_DM,
                   SER_ROOT_PW: PW_DM,
                   SER_HOST: LOCALHOST,
                   SER_PORT: DEFAULT_PORT,
                   SER_SERVERID_PROP: "template",
                   SER_CREATION_SUFFIX: DEFAULT_SUFFIX}

# Helper for linking dse.ldif values to the parse_config function
args_dse_keys = {
                SER_HOST: 'nsslapd-localhost',
                SER_PORT: 'nsslapd-port',
                SER_SECURE_PORT: 'nsslapd-secureport',
                SER_ROOT_DN: 'nsslapd-rootdn',
                #SER_ROOT_PW         (bindpw) We can't do this
                SER_CREATION_SUFFIX: 'nsslapd-defaultnamingcontext',
                SER_USER_ID: 'nsslapd-localuser',
                #SER_SERVERID_PROP   (serverid) Already have this set in other areas.
                #SER_GROUP_ID        (groupid) ???
                #SER_DEPLOYED_DIR    (prefix) Already provided to do the discovery
                #SER_BACKUP_INST_DIR (backupdir) nsslapd-bakdir <<-- maybe?
}
