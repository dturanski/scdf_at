#Install required POSTGRESQL lib for python
PATH=$PATH:~/.local/bin
python3 -m pip install --upgrade pip | grep -v 'Requirement already satisfied'
pip3 install -r requirements.txt | grep -v 'Requirement already satisfied'
#Install cf cli
os=$(uname)
if [[ "$os" == "Linux" ]]; then
    if ! command -v cf &> /dev/null
    then
      wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
      echo "deb https://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
      sudo apt-get update
      sudo apt-get install cf-cli
    fi
    if [[ "$SQL_PROVIDER" == "oracle" ]]; then
      echo "Installing ORACLE components"
       wget -q https://download.oracle.com/otn_software/linux/instantclient/215000/instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip
       unzip instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip
       export LD_LIBRARY_PATH=./instantclient_21_5
    fi
fi

export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_URL=https://api.sys.avenal.cf-app.com
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_ORG=p-dataflow
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SPACE=dturanski
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_DOMAIN=apps.avenal.cf-app.com
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_USERNAME=admin
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_PASSWORD=ElG6MlOlU20S-7K0Q5nkYa5wSBn9FdCY
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SKIP_SSL_VALIDATION=true
export SPRING_CLOUD_DEPLOYER_CLOUDFOUNDRY_SCHEDULER_URL=''
export SPRING_CLOUD_DATAFLOW_FEATURES_STREAMS_ENABLED=true
export SPRING_CLOUD_DATAFLOW_FEATURES_TASKS_ENABLED=true

python3 src/main.py $@