import { RouterProvider } from "react-router";
import { router } from "./routes";
import { UserTypeProvider } from "./context/UserTypeContext";
import { JobProvider } from "./context/JobContext";

export default function App() {
  return (
    <JobProvider>
      <UserTypeProvider>
        <RouterProvider router={router} />
      </UserTypeProvider>
    </JobProvider>
  );
}
