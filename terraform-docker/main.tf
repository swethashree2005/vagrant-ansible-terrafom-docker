terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ✅ Pull Nginx image
resource "docker_image" "nginx_image" {
  name         = "nginx:latest"
  keep_locally = false
}

# ✅ Pull Redis image
resource "docker_image" "redis_image" {
  name         = "redis:latest"
  keep_locally = false
}

# ✅ Create Nginx container
resource "docker_container" "nginx_container" {
  name  = "nginx-server"
  image = docker_image.nginx_image.image_id

  ports {
    internal = 80
    external = 8081
  }
}

# ✅ Create Redis container
resource "docker_container" "redis_container" {
  name  = "redis-server"
  image = docker_image.redis_image.image_id

  ports {
    internal = 6379
    external = 6379
  }
}
