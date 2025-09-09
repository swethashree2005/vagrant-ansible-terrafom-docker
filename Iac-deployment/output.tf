output "quiz_app_url" {
  value = "http://${data.external.host_ip.result["ip"]}:${var.app_port}"
}