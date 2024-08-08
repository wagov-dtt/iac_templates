#!/bin/bash

# Set variables
IAM_USER_NAME="rancher-user"
POLICY_ARNS=(
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
    "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"
    "arn:aws:iam::aws:policy/AmazonRoute53FullAccess"
)

# Create IAM user
aws iam create-user --user-name $IAM_USER_NAME

# Attach managed policies to user
for arn in "${POLICY_ARNS[@]}"; do
    aws iam attach-user-policy --user-name $IAM_USER_NAME --policy-arn $arn
done

# Create access key
ACCESS_KEY=$(aws iam create-access-key --user-name $IAM_USER_NAME --query 'AccessKey.[AccessKeyId,SecretAccessKey]' --output text)

echo "IAM user created successfully with comprehensive policies for Rancher."
echo "Access Key ID: $(echo $ACCESS_KEY | cut -f1)"
echo "Secret Access Key: $(echo $ACCESS_KEY | cut -f2)"
echo "Please save these credentials securely. You won't be able to retrieve the secret key again."