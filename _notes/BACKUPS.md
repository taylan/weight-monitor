### Backup Procedure

I changed databases from Amazon AWS to Heroku (because Heroku is cheaper [free])
I went through some odd issues while restoring the db dump to Heroku.
I'm writing this so I won't have to figure out how to do all this the next time I might have to change databases.


1. Backup database
    - No owner or privilege information (because I might not be able to create the same owners and privileges in the next database)
    - All data inserts done with regular INSERT statements rather than COPY statements.

    `pg_dump --no-privileges --no-owner --inserts -h DB_HOST DB_NAME -U DB_USER -W > DB_NAME-DATE.bak.sql`

2. Open .sql file and comment out everything that mentions 'plpgsql'
    - We backup the database as a plain sql file rather than a tar file because of this requirement to manually edit the sql

3. Restore database via psql
    - pg_restore is not used because the backup is a series of plain sql statements
    - The parameters tell psgl to run all statements as a single transaction

    `pgsql -h DB_HOST -U DB_USER -d DB_NAME -1  < BACKUP_FILE_PATH`
