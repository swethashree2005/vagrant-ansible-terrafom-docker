variable "vm_ip" {
  type        = string
  description = "Vagrant VM private_network IP"
  default     = "192.168.56.10"  # keep here or in terraform.tfvars
}

variable "app_port" {
  type        = number
  description = "App port inside the VM (guest port)"
  default     = 8080
}
