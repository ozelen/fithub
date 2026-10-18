// Deploy job `labhub-deploy`: Pipeline from SCM, this file. Triggered by GitHub Actions with IMAGE_TAG (git SHA).
// Jenkins credential ID must be `ozelen` (SSH Username with private key). Never put a key in this repo.
pipeline {
  agent any
  parameters {
    string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Image tag from GitHub Actions (git SHA)')
  }
  stages {
    stage('Deploy') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'ozelen', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          sh '''
            set -eu
            TAG="${IMAGE_TAG:?IMAGE_TAG required}"
            ssh -i "$SSH_KEY" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new \
              "${SSH_USER}@192.168.1.185" "bash -s -- ${TAG}" <<'REMOTE'
            set -eu
            cd /
            K="sudo k3s kubectl"
            TAG="${1:?IMAGE_TAG required}"
            ns=ix-fithub
            for deploy in $($K -n "$ns" get deploy -o jsonpath='{.items[*].metadata.name}'); do
              container="$($K -n "$ns" get deploy "$deploy" -o jsonpath='{.spec.template.spec.containers[0].name}')"
              echo "set $ns/$deploy $container=zelenuk/fithub:$TAG"
              $K -n "$ns" set image "deploy/$deploy" "$container=zelenuk/fithub:$TAG"
              $K -n "$ns" rollout status "deploy/$deploy" --timeout=180s
            done
REMOTE
          '''
        }
      }
    }
  }
}
