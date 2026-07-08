### Run event generator

```shell
pip install -r requirements.txt
docker compose up -d
python -m src.generator.main
```

### Run event consumer

```shell
pip install -r requirements.txt
docker compose up -d
python -m src.consumer.main
```
