NRW AI Pipeline Evidence Bundle

Contents:
- 01_setup.log .. 08_deploy_api.log: Logs per stage
- models/*_metrics.json: Per-modality metrics
- models/*_predictions.parquet: Evaluation prediction tables
- fusion/*: Fusion metrics, details, fused predictions, detection_delays
- quality/*_profile.json: Data quality profiles per dataset/features
- openapi.json: API contract snapshot
- api_health.json, api_predict.json: Health check and sample inference response
- sample_predict_request.json: Payload used for inference

Notes:
- Acoustic training was skipped; fusion evaluated available modalities.
- API /predict_frame inferred spectrogram via audio_b64; errors may be due to librosa/numba caching in container.
