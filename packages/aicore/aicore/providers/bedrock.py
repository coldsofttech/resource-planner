from __future__ import annotations

import json

import boto3


class BedrockProvider:
    """Calls an Anthropic model hosted on AWS Bedrock.

    auth_mode="role"  — boto3 resolves credentials via instance profile / ECS
                        task role / AWS_* environment variables.
    auth_mode="user"  — explicit IAM user access key + secret are used.
    """

    def __init__(
        self,
        model: str,
        region: str,
        auth_mode: str = "role",
        iam_key: str = "",
        iam_secret: str = "",
    ) -> None:
        self._model = model
        kwargs: dict = {"region_name": region}
        if auth_mode == "user" and iam_key and iam_secret:
            kwargs["aws_access_key_id"] = iam_key
            kwargs["aws_secret_access_key"] = iam_secret
        self._client = boto3.client("bedrock-runtime", **kwargs)

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response = self._client.invoke_model(
            modelId=self._model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"].strip()
