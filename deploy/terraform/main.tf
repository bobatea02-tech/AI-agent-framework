provider "aws" {
  region = "us-west-2"
}

resource "aws_vpc" "agent_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "ai-agent-vpc"
  }
}

resource "aws_eks_cluster" "main" {
  name     = "ai-agent-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = aws_subnet.public[*].id
  }
}

resource "aws_db_instance" "default" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.micro"
  db_name              = "agent_framework"
  username             = "postgres"
  password             = "change_me_in_prod"
  skip_final_snapshot  = true
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "agent-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
}
