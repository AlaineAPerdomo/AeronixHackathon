# AI Development Rules

This document outlines the technology stack and development guidelines for the AI assistant working on this project. Following these rules ensures consistency, maintainability, and adherence to best practices.

## Tech Stack

*   **Frontend Framework**: React with Vite for a fast and modern development experience.
*   **Language**: TypeScript for type safety and robust code.
*   **Styling**: Tailwind CSS for a utility-first, responsive design approach.
*   **UI Components**: **shadcn/ui** is the primary component library. It's built on Radix UI and Tailwind CSS, offering accessible and customizable components.
*   **Icons**: `lucide-react` for a clean and consistent set of icons.
*   **Routing**: React Router (`react-router-dom`) for all client-side navigation.
*   **Backend Logic**: Python for data processing, document analysis, and interacting with AI models and external APIs.
*   **Core Python Libraries**: LangChain for AI orchestration, Google Generative AI for model access, ChromaDB for vector storage, and Tavily for web search.

## Library and Component Usage Rules

### Frontend Development

*   **UI Components**:
    *   **Default to shadcn/ui**: Before creating a new component, always check if a suitable one exists in the `shadcn/ui` library.
    *   **Custom Components**: If a custom component is needed, it must be created as a small, single-purpose file in `src/components/`. Style it exclusively with Tailwind CSS.
    *   **No Other UI Libraries**: Do not install other component libraries like Material-UI or Ant Design.

*   **Styling**:
    *   **Tailwind CSS Only**: All styling must be done with Tailwind utility classes.
    *   **No Custom CSS Files**: Avoid writing separate `.css` files. All styles should be co-located with the JSX.
    *   **Responsive Design**: All components and layouts must be responsive, using Tailwind's breakpoint variants (e.g., `sm:`, `md:`, `lg:`).

*   **Icons**:
    *   Use icons exclusively from the `lucide-react` package to maintain visual consistency.

*   **State Management**:
    *   **Local State**: Use React's built-in hooks (`useState`, `useReducer`).
    *   **Global State**: Start with `useContext` for simple global state. Avoid adding complex libraries like Redux or Zustand unless the application's complexity demands it.

*   **Routing**:
    *   Define all routes in `src/App.tsx` using `react-router-dom`.
    *   New pages should be created as components within the `src/pages/` directory.

### Backend Development

*   **Separation of Concerns**: The Python scripts in `src/` are responsible for all heavy lifting, including file processing, AI model interaction, and external API calls. The frontend should not contain this logic.
*   **API Layer**: The frontend will communicate with the Python backend through a REST API. (This API will need to be built to expose the Python functionality).
*   **Environment Variables**: All secrets and API keys (like `GOOGLE_API_KEY`) must be managed through a `.env` file and accessed via `os.environ`. Do not hard-code them.