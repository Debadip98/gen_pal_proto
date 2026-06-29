import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { LandingPage } from "./screens/LandingPage";
import { DocsDiscovery } from "./screens/DocsDiscovery";
import { GenerationProgress } from "./screens/GenerationProgress";
import { RequestorDashboard } from "./screens/RequestorDashboard";
import { SendToSME } from "./screens/SendToSME";
import { SMEReviewLanding } from "./screens/SMEReviewLanding";
import { SMEQuestionReview } from "./screens/SMEQuestionReview";
import { RegenerateQuestion } from "./screens/RegenerateQuestion";
import { VersionComparison } from "./screens/VersionComparison";
import { DocCheckPanel } from "./screens/DocCheckPanel";
import { SMEReviewComplete } from "./screens/SMEReviewComplete";
import { ExcelDownloadCenter } from "./screens/ExcelDownloadCenter";
import { CostDashboard } from "./screens/CostDashboard";
import { BusinessFlow } from "./screens/BusinessFlow";
import { DuplicateReview } from "./screens/DuplicateReview";
import { QuestionPreview } from "./screens/QuestionPreview";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: LandingPage },
      { path: "docs", Component: DocsDiscovery },
      { path: "progress", Component: GenerationProgress },
      { path: "dashboard", Component: RequestorDashboard },
      { path: "send-review", Component: SendToSME },
      { path: "sme-review", Component: SMEReviewLanding },
      { path: "sme-question", Component: SMEQuestionReview },
      { path: "regenerate", Component: RegenerateQuestion },
      { path: "version-compare", Component: VersionComparison },
      { path: "doc-check", Component: DocCheckPanel },
      { path: "review-complete", Component: SMEReviewComplete },
      { path: "export", Component: ExcelDownloadCenter },
      { path: "cost", Component: CostDashboard },
      { path: "flow", Component: BusinessFlow },
      { path: "duplicates", Component: DuplicateReview },
      { path: "preview", Component: QuestionPreview },
    ],
  },
]);
