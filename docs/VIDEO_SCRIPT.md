# Video Demo Script - 5 Minutes

## 0:00 - 0:30: Introduction
*   **Visual**: Title Slide "AI Agent Framework".
*   **Audio**: "Hi, we are presenting the AI Agent Framework, an enterprise-grade solution for orchestrating intelligent agents. It solves the problem of complexity and latency in building AI workflows."

## 0:30 - 1:30: Architecture & Intel Integration
*   **Visual**: Architecture Diagram (Mermaid).
*   **Audio**: "Our system is event-driven using Kafka. The secret sauce is our integration with **Intel OpenVINO**, which allows us to run heavy AI models like OCR on standard CPUs with GPU-like performance."
*   **Action**: Show `scripts/optimize_with_openvino.py` code briefly.

## 1:30 - 3:00: Interactive Demo (The "Wow" Moment)
*   **Visual**: Terminal with `scripts/interactive_demo.py`.
*   **Action**: 
    1.  Run `python scripts/interactive_demo.py`.
    2.  Select "1. Check System Health" -> Show all green.
    3.  Select "3. Run Intel OpenVINO OCR Demo".
    4.  Show the "Speedup" logs in terminal.
    5.  Open `demo_result.jpg` to show Visual Comparison.
*   **Audio**: "Here we compare standard Tesseract against OpenVINO. As you can see, we achieve a 5x speedup, dropping latency from 1.2s to under 300ms."

## 3:00 - 4:00: Workflows & Observability
*   **Visual**: Grafana Dashboard / Airflow UI.
*   **Action**: Select "5. Open Grafana" in menu. Show the "Throughput" graphs.
*   **Audio**: "This isn't just a prototype. It's production-ready with full observability, rate limiting, and security built-in."

## 4:00 - 5:00: Conclusion
*   **Visual**: Presentation Slide "Future Roadmap".
*   **Audio**: "We are ready to scale. With Intel OpenVINO, we can deploy this on edge devices or cloud CPUs cost-effectively. Thank you."
