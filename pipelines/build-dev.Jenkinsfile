
// pipelines/build.Jenkinsfile
def IMAGE_FULL_NAME_PARAM
pipeline {
    agent {
        label 'general'
    }
    
    triggers {
        githubPush()
    }

        options {
        timeout(time: 10, unit: 'MINUTES')  // discard the build after 10 minutes of running
        timestamps()  // display timestamp in console output
    }

        environment {
        // GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        // TIMESTAMP = new Date().format("yyyyMMdd-HHmmss")

        IMAGE_TAG = "dev_v0.2.$BUILD_NUMBER"
        IMAGE_BASE_NAME = "int-polybot"

        DOCKER_CREDS = credentials('dockerhub')
        DOCKER_USERNAME = "${DOCKER_CREDS_USR}"  // The _USR suffix added to access the username value
        DOCKER_PASS = "${DOCKER_CREDS_PSW}"      // The _PSW suffix added to access the password value
    }

    stages {
        stage('Docker setup') {
            steps {
                sh '''
                  docker login -u $DOCKER_USERNAME -p $DOCKER_PASS
                '''
            }
        }

        stage('Build app container') {
            steps {
                sh '''
                    IMAGE_FULL_NAME=$DOCKER_USERNAME/$IMAGE_BASE_NAME:$IMAGE_TAG
                    # your pipeline commands here....
                    
                    # for example list the files in the pipeline workdir
                    ls 
                    
                    # build an image
                    docker build -t $IMAGE_FULL_NAME polybot/
                    docker push $IMAGE_FULL_NAME
                    echo -n $IMAGE_FULL_NAME > IMAGE_FULL_NAME.txt
                '''
                script {
                    IMAGE_FULL_NAME_PARAM = readFile('IMAGE_FULL_NAME.txt')
                }
            }
        }
        stage('Trigger Deploy') {
            steps {
                build job: 'deploy_dev', wait: false, parameters: [
                string(name: 'SERVICE_NAME', value: "polybot"),
                string(name: 'IMAGE_FULL_NAME_PARAM', value: "$IMAGE_FULL_NAME_PARAM")
                ]
            }
        }
    }
}
