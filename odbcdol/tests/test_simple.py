from odbcdol import SQLServerPersister


def test_sqlserver_persister():
    sql_server_persister = SQLServerPersister()

    print("Fetching a Record")
    print(sql_server_persister[1])
    print(sql_server_persister[3])
    print("=========================")

    print("Adding a Record")
    sql_server_persister[3] = {"id": "3", "name": "new name"}
    sql_server_persister[4] = {"id": "4", "name": "Hamid NEW"}
    sql_server_persister[5] = {"id": "5", "name": "Hamid NEW AGAIN"}

    print(sql_server_persister[3])
    print(sql_server_persister[4])
    print(sql_server_persister[5])
    print("======================")

    print("Deleting a Record")
    del sql_server_persister[3]
    del sql_server_persister[4]
    del sql_server_persister[5]
    print(sql_server_persister[3])
    print("=====================")

    print("Iterating over the records")
    for record in sql_server_persister:
        print(record)
    print("=========================")

    print("Getting the length")
    print(len(sql_server_persister))
