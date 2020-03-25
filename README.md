#How to run:

- cd docker && docker-compose up -d
- Go to `localhost:8080`
- Update default postgres connection: 
go to `Admin -> Connection -> postgres_default`, change `schema`, `login`, `password` to `airflow`
- Unpause and trigger dags

In order trigger_dag to progress file should be added to directory: 
- In terminal: `docker ps`
- Choose row with name `docker_worker_1` and copy its `container id`
- In terminal: `docker exec -it place_here_copied_container_id /bin/bash`
- In terminal: `touch /tmp/run`
