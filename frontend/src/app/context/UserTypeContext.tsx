import { createContext, useContext, useState } from "react";

type UserType = "requestor" | "sme";

interface UserTypeContextValue {
  userType: UserType;
  setUserType: (type: UserType) => void;
}

const UserTypeContext = createContext<UserTypeContextValue | null>(null);

export function UserTypeProvider({ children }: { children: React.ReactNode }) {
  const [userType, setUserType] = useState<UserType>("requestor");
  return (
    <UserTypeContext.Provider value={{ userType, setUserType }}>
      {children}
    </UserTypeContext.Provider>
  );
}

export function useUserType() {
  const ctx = useContext(UserTypeContext);
  if (!ctx) throw new Error("useUserType must be used inside UserTypeProvider");
  return ctx;
}
