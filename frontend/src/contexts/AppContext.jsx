// contexts/AppContext.jsx — Thin app-wide context stub
import { createContext, useContext } from 'react';

const AppContext = createContext({});

export function AppProvider({ children }) {
  return <AppContext.Provider value={{}}>{children}</AppContext.Provider>;
}

export const useApp = () => useContext(AppContext);

export default AppContext;
