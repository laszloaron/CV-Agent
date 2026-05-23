import os
from pydantic_ai.models.instrumented import InstrumentationSettings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from openinference.instrumentation.pydantic_ai import OpenInferenceSpanProcessor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


# Global instrumentation settings for Pydantic AI
instrumentation = InstrumentationSettings(version=2)

def setup_monitoring():
    """Initializes OpenTelemetry tracing and points it to Arize Phoenix."""
    # Set up TracerProvider
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

    # Set up Arize Phoenix endpoint
    phoenix_endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")

    # Add OpenInference and OTLP exporters
    tracer_provider.add_span_processor(OpenInferenceSpanProcessor())
    exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))

    print(f"Monitoring initialized. Sending traces to {phoenix_endpoint}")
