resource "local_file" "example" {
  content  = "Hello from Terraform!"
  filename = "hello.txt"
}
