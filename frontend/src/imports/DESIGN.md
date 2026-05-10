# Design System: GPA Goes 📈

## Global Rules
* **Theme:** Light Mode, earthy, calming, and friendly ("gamified productivity"). 
* **Typography:** Use the `Nunito` font family for all text to maintain a rounded, approachable feel.
* **Border Radius:** Use heavily rounded corners (e.g., `rounded-2xl` or `rounded-3xl` in Tailwind) for all cards, buttons, and input fields to support the gamified aesthetic. No sharp corners.
* **Shadows:** Use very soft, diffused drop shadows with warm earthy tints. Do not use harsh black shadows.
* **Layout:** Highly structured, breathable, with ample padding (`p-6` or `p-8` minimum inside cards).

## Color Palette (Tailwind Mapping)
* **Background (Canvas):** `#DEDBD2`
* **Surfaces (Cards, Modals, Upload Areas):** `#EAE3CD`
* **Primary Text (Body):** `#4F5321`
* **Secondary Text & Headings:** `#88734B`
* **Primary Brand / Action (Buttons, Active Tabs):** `#A8BE83`
* **Success / "Goes Up" Metrics:** `#9CA35A`
* **Soft Highlights (Backgrounds for success items):** `#C2D0B9`
* **Warnings / Alternative Options:** `#F2C27F`
* **Critical Alerts:** `#C87330`

## Components
* **Buttons:** Chunky, pill-shaped, or heavily rounded. Primary buttons use the `#A8BE83` background with white or `#4F5321` text. 
* **Cards:** `#EAE3CD` background, no borders, soft shadow, `rounded-3xl`.
* **Chatbot FAB:** A persistent floating action button in the bottom right corner.