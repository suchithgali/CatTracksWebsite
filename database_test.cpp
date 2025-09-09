#include <iostream>
#include <libpq-fe.h>

int main(){
    
    PGconn* conn = PQconnectdb("dbname = cattracks user = postgres password = 2005 host = localhost");
    if (PQstatus(conn) != CONNECTION_OK){
        std::cerr << "Connection failed: " << PQerrorMessage(conn) << "\n";
        PQfinish(conn);
        return 1;
    }

    /*PGconn* conn = PQconnectdb("dbname=cattracks user=postgres password=2005 host=localhost");
    if (PQstatus(conn) != CONNECTION_OK) {
    std::cerr << "Connection failed: " << PQerrorMessage(conn) << "\n";
    PQfinish(conn);
    return 1;
    }
    */

    const char* createTableSQL = R"(
    CREATE TABLE IF NOT EXISTS cattracks (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL
    );
    
    )";

    /*const char* insertSQL = R"(
    INSERT INTO cattracks (username, email) VALUES
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com'),
    ('bob_jones', 'bob@examples.com');
    )";
    */

    const char* deleteSQL = "DELETE FROM cattracks WHERE username = 'bob_jones';";

    PGresult* res = PQexec(conn, createTableSQL);
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        std::cerr << "Table creation failed: " << PQerrorMessage(conn) << "\n";
    }
    PQclear(res);

    // Execute the INSERT statement
    /*res = PQexec(conn, insertSQL);
    if (PQresultStatus(res) != PGRES_COMMAND_OK) {
        std::cerr << "Insert failed: " << PQerrorMessage(conn) << "\n";
    } else {
        std::cout << "Data inserted successfully!\n";
    }
    PQclear(res);
    */

    res = PQexec(conn, deleteSQL);
    if (PQresultStatus(res) != PGRES_COMMAND_OK){
        std::cerr << "Delete failed: " << PQerrorMessage(conn) << "\n";
    }
    else{
        std::cout << "Data deleted successfully!\n";
    }
    PQclear(res);

    PQfinish(conn);
    return 0;
}
