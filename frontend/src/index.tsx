// frontend/src/index.tsx
// 這是React應用程式的入口檔案，負責啟動整個前端應用

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// 建立React應用程式的根節點
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// 渲染整個應用程式
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);