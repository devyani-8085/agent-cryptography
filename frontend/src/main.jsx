import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import CryptoLab from './CryptoLab.jsx'

const Page = window.location.hash === '#/crypto-lab' ? CryptoLab : App

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Page />
  </StrictMode>,
)
