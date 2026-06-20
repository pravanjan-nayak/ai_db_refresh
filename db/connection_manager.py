import oracledb
from config.environments import get_environment
from config.oracle_config import TNS_ADMIN

# Tell python-oracledb where tnsnames.ora is located
oracledb.defaults.config_dir = TNS_ADMIN


def get_connection(env_name, target_pdb: str = None, session_user: str = None, ticket_id: str = None):
    """
    Establishes a connection to the specified Oracle environment.
    
    Optional Enhancements:
    - target_pdb: Dynamic multitenant container switching via ALTER SESSION.
    - session_user: Human DBA identifier passed into the database kernel for auditing.
    - ticket_id: Operational Change Management reference ID for traceability tracking.
    """
    env = get_environment(env_name)

    if not env:
        raise Exception(
            f"Unknown environment: {env_name}"
        )

    # Establish the base connection to the target DSN (usually hits CDB$ROOT or a default service)
    conn = oracledb.connect(
        user="system",
        password="tiger",
        dsn=env["tns"]
    )

    cursor = conn.cursor()

    try:
        # 1. 🌟 MULTI-TENANT CONTAINER CONTEXT SWITCHING
        # If a specific Pluggable Database is targeted, switch the session context immediately
        if target_pdb and target_pdb.upper() != "CDB$ROOT":
            # Sanitize the PDB name to prevent syntax errors
            clean_pdb = "".join(c for c in target_pdb if c.isalnum() or c in ('_', '#', '$')).upper()
            cursor.execute(f'ALTER SESSION SET CONTAINER = "{clean_pdb}"')

        # 2. 🌟 TOKEN-BASED SESSION AUDITING AND TRACEABILITY
        # If audit credentials are provided from the UI layer, stamp them directly into v$session memory
        if session_user:
            # Set the Client Identifier attribute (visible in V$SESSION.CLIENT_IDENTIFIER)
            conn.client_identifier = str(session_user).upper()
            
            # Formulate the module and action components for DBMS_APPLICATION_INFO
            module_name = f"AI_AGENT_{str(ticket_id).upper()}" if ticket_id else "AI_DBA_AGENT"
            action_name = "SOP_EXECUTION" if target_pdb else "DYNAMIC_QUERY"
            
            # Call the standard Oracle database dictionary auditing utility package
            cursor.callproc("DBMS_APPLICATION_INFO.SET_MODULE", [module_name, action_name])

    except oracledb.DatabaseError as e:
        # If an internal context initialization fails, tear down the network pool socket cleanly
        cursor.close()
        conn.close()
        error_obj, = e.args
        raise Exception(
            f"Database Context Initialization Failed! | Oracle Error: {error_obj.message}"
        )
        
    finally:
        # Always close the temporary context configuration cursor before returning the connection
        if not cursor.isclosed():
            cursor.close()

    return conn