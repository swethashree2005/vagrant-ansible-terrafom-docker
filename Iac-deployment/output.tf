# output "quiz_app_url" {
#   value = "http://${data.external.host_ip.result["ip"]}:${var.app_port}"
# }

output "quiz_app_url" {
  value = "http://${var.vm_ip}:${var.app_port}"
}