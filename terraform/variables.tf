variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "weather-data-viz"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-north-1"
}
