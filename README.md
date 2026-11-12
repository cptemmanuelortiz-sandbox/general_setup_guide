# 📋 Universal Process Guide Generator

A lightweight, Python-based static site generator (SSG) designed to create interactive, bilingual, step-by-step guides for any process (e.g., IT onboarding, equipment setup, HR procedures).

## 🚀 The Problem
Organizations often rely on outdated PDFs or static wikis for internal processes. These are hard to maintain, impossible to translate instantly, and don't support embedded video tutorials.

## 💡 The Solution
This tool converts a simple `config.json` data file into a fully responsive, dual-language HTML website with smart routing.

## ✨ Core Features
- **Dynamic Routing:** Define multiple paths (e.g., "Mac User" vs "Windows User") in JSON. The script automatically builds a choice selection page.
- **Zero-Dependency Frontend:** Pure HTML/CSS/Vanilla JS. No React, no Node.js build steps required.
- **Bilingual Engine:** Toggle between English and Spanish instantly. Uses `localStorage` to remember user preference across pages, but resets on entry.
- **Multimedia Support:** Embeds YouTube and Google Drive videos seamlessly alongside images.
- **CI/CD Ready:** Includes a `deploy.yml` GitHub Action that automatically builds and deploys the site to GitHub Pages on every push.

## 🛠️ Architecture
- **Backend:** Python (parses JSON, generates static HTML templates).
- **Frontend:** HTML5, CSS Grid/Flexbox, Vanilla JS.
- **Deployment:** GitHub Actions, GitHub Pages.

## ⚙️ How to Use This Template
1. Click the **"Use this template"** button at the top of this repo.
2. Edit `config.json` to define your processes and steps.
3. Drop your images into `static/images/`.
4. Push to the `main` branch. The GitHub Action will handle the rest.

*Built to demonstrate data-driven static site generation, i18n (internationalization) logic, and CI/CD pipeline automation.*
