default: run

run: schema
	python bouncer.py

schema: bouncer.db

bouncer.db: schema.sql
	sqlite3 bouncer.db < schema.sql
