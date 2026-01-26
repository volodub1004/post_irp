# PostGres Setup

Notes for setting up POSTGRE. 

# Basic Start

Basic apt installs.

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```
Start the service and check the status.

```bash
sudo service postgresql start
sudo service postgresql status
```

Creating a database.

```bash
# Open psql prompt
sudo -u postgres psql
```

then in prompt,

```sql
CREATE DATABASE irpdb;
\q
```

Then we can migrate and bring up studio

```bash
npx prisma migrate dev --name init
npx prisma generate
npx prisma studio
```

Run the init script, this will fill from the seed file.

```bash
./scripts/init_db.sh
```


# Wiping and starting from clean

Probably, most importantly, how to start again after things get messy.

This ends any sessions that might be alive and stopping you from deleting a table.

```bash
sudo -u postgres psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='irpdb' AND pid<>pg_backend_pid();"
```

```bash
# Bring up psql prompt
sudo -u postgres psql
```

Then in prompt:

```sql
DROP DATABASE IF EXISTS irpdb;
CREATE DATABASE irpdb;
\q
```

Drop the database. Should be brand new and empty now.
To be safe, drop migration history and generated client code.

```bash
rm -rf prisma/migrations
rm -rf src/generated/prisma
```

Check the ENV file to make sure that it works as expected.

```bash
DATABASE_URL="postgresql://postgres:test@localhost:5432/irpdb"
```

| Segment         | Meaning                               | Example                                        |
| --------------- | ------------------------------------- | ---------------------------------------------- |
| `postgresql://` | Protocol — always this for Postgres   | (literal)                                      |
| `username`      | Your Postgres user (often `postgres`) | `postgres`                                     |
| `password`      | Your password for that user           | `test`                             |
| `host`          | Where Postgres is running             | `localhost` (if local), or IP/domain if remote |
| `port`          | Default Postgres port                 | `5432`                                         |
| `database_name` | The actual database you’ll use        | `irpdb`, `investor_db`, etc.                   |

Now we can run a fresh migration.

```bash
npx prisma migrate dev --name init
```

We can confirm success by running the studio and visiting http://localhost:5555 in the browser.

```bash
npx prisma studio
```

## Killing old ports

Check the stray port

```bash
sudo ss -lptn 'sport = :3000'
```

Replace 3000 with whatever the port is (default 3000 for npm run dev).

Then kill the pid that it returns.

```bash
kill -9 54731
```