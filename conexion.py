

import mysql.connector
from mysql.connector import Error
import os

def conectar():
    try:
        return mysql.connector.connect(
            host="gateway01.ap-northeast-1.prod.aws.tidbcloud.com",
            port=4000,
            user="29PVtw1CRqJY1nx.root",
            password=os.environ.get("TIDB_PASSWORD"),
            database="biblioteca_escolar",
            ssl_ca=os.path.join(os.path.dirname(os.path.dirname(__file__)), "isrgrootx1.pem"),
            ssl_verify_cert=True
        )

    except Error as error:
        print("No se pudo conectar con TiDB:", error)
        return None
