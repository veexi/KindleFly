import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      hasError: true,
      error: error,
      errorInfo: errorInfo
    });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', background: '#0a0a0f', color: '#f3f4f6', height: '100vh', overflow: 'auto', fontFamily: 'monospace' }}>
          <h2 style={{ color: '#ef4444', marginBottom: '16px', fontFamily: 'sans-serif' }}>⚠️ 软件界面运行异常崩溃</h2>
          <p style={{ marginBottom: '10px', fontWeight: 'bold' }}>错误类型: {this.state.error && this.state.error.toString()}</p>
          <pre style={{ background: '#101016', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)', whiteSpace: 'pre-wrap', fontSize: '13px', lineHeight: '1.6', color: '#9ca3af' }}>
            {this.state.errorInfo && this.state.errorInfo.componentStack}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '20px', padding: '10px 20px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            重新加载界面
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
