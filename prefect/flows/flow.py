from prefect import flow, task

@task
def read_from_rds():
    # Read and transform data
    return labelled_documents

@task
def post_to_api(labelled_documents):
    # Post to API, store in RDS
    pass

@task
def send_to_vespa(labelled_documents):
    # Index in Vespa
    pass

@flow
def pipeline():
    docs = read_from_rds()
    post_to_api(docs)
    send_to_vespa(docs)

if __name__ == "__main__":
    pipeline()
