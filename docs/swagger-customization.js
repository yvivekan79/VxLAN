
// Custom Swagger UI styling and configuration
window.onload = function() {
  // Custom CSS for Swagger UI
  const style = document.createElement('style');
  style.textContent = `
    .swagger-ui .topbar {
      background-color: #1f2937;
      border-bottom: 3px solid #3b82f6;
    }
    
    .swagger-ui .topbar .download-url-wrapper .select-label {
      color: #ffffff;
    }
    
    .swagger-ui .info {
      margin: 50px 0;
    }
    
    .swagger-ui .info .title {
      color: #1f2937;
      font-size: 36px;
      font-weight: bold;
    }
    
    .swagger-ui .info .description {
      color: #374151;
      font-size: 16px;
      line-height: 1.6;
    }
    
    .swagger-ui .scheme-container {
      background: #f8fafc;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 15px;
      margin: 20px 0;
    }
    
    .swagger-ui .opblock.opblock-post {
      border-color: #059669;
      background: rgba(5, 150, 105, 0.1);
    }
    
    .swagger-ui .opblock.opblock-get {
      border-color: #3b82f6;
      background: rgba(59, 130, 246, 0.1);
    }
    
    .swagger-ui .opblock.opblock-delete {
      border-color: #dc2626;
      background: rgba(220, 38, 38, 0.1);
    }
    
    .swagger-ui .opblock.opblock-put {
      border-color: #f59e0b;
      background: rgba(245, 158, 11, 0.1);
    }
    
    .swagger-ui .opblock-tag {
      font-size: 18px;
      font-weight: bold;
      color: #1f2937;
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 10px;
    }
    
    .swagger-ui .opblock-summary-path {
      font-family: 'Monaco', 'Courier New', monospace;
      font-weight: bold;
    }
    
    .swagger-ui .parameter__name {
      font-weight: bold;
    }
    
    .swagger-ui .response-col_status {
      font-weight: bold;
    }
  `;
  document.head.appendChild(style);
  
  // Add custom header
  const header = document.createElement('div');
  header.innerHTML = `
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
      <h1 style="margin: 0; font-size: 28px;">🌐 VxLAN Tunnel Management API</h1>
      <p style="margin: 10px 0 0 0; opacity: 0.9;">Comprehensive REST API for VxLAN tunnel and network topology management</p>
    </div>
  `;
  
  const infoContainer = document.querySelector('.swagger-ui .info');
  if (infoContainer && infoContainer.parentNode) {
    infoContainer.parentNode.insertBefore(header, infoContainer);
  }
};
