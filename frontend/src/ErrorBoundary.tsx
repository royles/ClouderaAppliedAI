import React, { Component, ErrorInfo, ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Customer 360 UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <section className="panel" style={{ margin: "1.5rem" }}>
          <h1>Something went wrong</h1>
          <p className="error">{this.state.error.message}</p>
          <p className="muted small">
            Try a hard refresh. If this persists, restart the application and confirm
            frontend/dist matches the running API version.
          </p>
          <button
            type="button"
            className="control control-btn"
            onClick={() => window.location.reload()}
          >
            Reload page
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}
