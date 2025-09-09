#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# --- Speed up apt globally ---
sudo tee /etc/apt/apt.conf.d/99-speed >/dev/null <<'EOF'
Acquire::Retries "5";
Acquire::http::Timeout "30";
Acquire::https::Timeout "30";
Acquire::ForceIPv4 "true";
Acquire::Languages "none";
APT::Install-Recommends "false";
Dpkg::Use-Pty "0";
Acquire::Queue-Mode "host";
EOF

# --- Use India mirror (IIT Kanpur) ---
sudo sed -i 's|http://us.archive.ubuntu.com/ubuntu|http://mirror.cse.iitk.ac.in/ubuntu|g' /etc/apt/sources.list || true
sudo apt-get clean

# --- Base tools (no update yet) ---
sudo apt-get install -y curl gnupg lsb-release ca-certificates software-properties-common || true

# --- Add official Docker repo ---
sudo mkdir -p /usr/share/keyrings
curl -fsSL --retry 5 --retry-delay 3 https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
| sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

# --- Single apt-get update (after all repos are ready) ---
sudo apt-get update -y

# --- Install only Docker Engine (skip compose plugins) ---
if timeout 180s sudo apt-get -o Acquire::Retries=5 -o Acquire::ForceIPv4=true \
    install -y docker-ce docker-ce-cli containerd.io; then
  DOCKER_SRC="docker.com"
else
  echo ">> Official Docker repo too slow, falling back to Ubuntu docker.io"
  sudo apt-get -f install -y || true
  sudo rm -f /etc/apt/sources.list.d/docker.list
  sudo apt-get update -y
  sudo apt-get install -y docker.io containerd runc
  DOCKER_SRC="ubuntu-mirror"
fi
set -e

# --- Enable & start ---
sudo systemctl enable --now docker

# --- Verify ---
docker --version || true
echo ">> Docker installed via: ${DOCKER_SRC}"
sudo usermod -aG docker vagrant



chown -R vagrant:vagrant /home/vagrant/terraform-docker

# # SSH key for Ansible
sudo -u vagrant ssh-keygen -t rsa -b 2048 -N "" -f /home/vagrant/.ssh/id_rsa || true

    # Setup Docker workers
# docker network create --subnet=172.20.0.0/24 ansible-net || true
# docker pull ubuntu:22.04
# for i in 1 2; do
#       cname="worker$i"
#       cip="172.20.0.1$i"
#       docker rm -f $cname || true
#       docker run -d --name $cname --hostname $cname \
#         --net ansible-net --ip $cip \
#         --privileged ubuntu:22.04 sleep infinity
#       docker exec $cname apt-get update
#       docker exec $cname apt-get install -y openssh-server python3 sudo
#       docker exec $cname mkdir -p /var/run/sshd /root/.ssh
#       docker exec $cname bash -c "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config"
#       docker exec $cname service ssh start
#       pubkey=$(cat /home/vagrant/.ssh/id_rsa.pub)
#       docker exec $cname bash -c "echo '${pubkey}' >> /root/.ssh/authorized_keys"
# done

# Setup Docker workers
docker network create --subnet=172.20.0.0/24 ansible-net || true
docker pull ubuntu:22.04

pubkey=$(cat /home/vagrant/.ssh/id_rsa.pub)

for i in 1 2; do
  cname="worker$i"
  cip="172.20.0.1$i"

  docker rm -f $cname || true
  docker volume create worker_ssh

  docker run -d --name $cname --hostname $cname \
  --net ansible-net --ip $cip \
  --privileged --restart=always \
  -v worker_ssh:/root/.ssh \
  ubuntu:22.04 sleep infinity

  docker exec $cname apt-get update
  docker exec $cname apt-get install -y openssh-server python3 sudo

  docker exec $cname mkdir -p /var/run/sshd /root/.ssh
  docker exec $cname bash -c "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config"

  # Add the VM's pubkey into root's authorized_keys safely
 # echo "$pubkey" | docker exec -i $cname tee /root/.ssh/authorized_keys > /dev/null
  echo "$pubkey"| docker exec -i $cname bash -c 'tee /root/.ssh/authorized_keys' > /dev/null

  # Fix SSH perms
  docker exec $cname chmod 700 /root/.ssh
  docker exec $cname chmod 600 /root/.ssh/authorized_keys

  # Restart ssh service
  docker exec $cname service ssh restart
done
