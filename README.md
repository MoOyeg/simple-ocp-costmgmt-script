# simple-ocp-costmgmt-script  

Simple OCP CostMgmt Use Cases.  
Repo to eventually provide a series of ancillary OCP costmgmt use cases.  

At the moment provides a simple script to help pull data from OCP costmgmt and label cluster projects with the cost of that specific project

## Requirements
- Python 3.10
- [Token from Red Hat](https://access.redhat.com/articles/3626371#bgenerating-an-access-tokenb-4)

## How to Run
- [Obtain and export your OFFLINE_TOKEN](https://access.redhat.com/articles/3626371#bgenerating-an-access-tokenb-4)
    ```bash
    export OFFLINE_TOKEN
    ```

- export your kubeconfig
  ```bash
  export KUBECONFIG=$KUBECONFIG_FILE    
  ```

- Install Applications
  ```bash
  pip install -r ./app/requirements.txt
  ```

- Run Application
  ```bash
  python ./app/app.py
  ```
