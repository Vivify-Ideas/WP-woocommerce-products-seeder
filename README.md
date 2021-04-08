# WP woocommerce products seeder

This was used as starting point
https://github.com/GabeWeiss/sql_data_randomizer


Run *-h* for full usage/options.
```bash
python mysql_faker.py -h
```

Dockerfile and deployment yaml files also handy to run this in a container if you want to scale it up with Kubernetes.

Example:
```bash
python mysql_faker.py -u root -p mypassword -d exampledb -P 3306 --number 100000
```
