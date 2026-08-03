import { useParams } from "react-router-dom";
import { VisitorSelector } from "@/pages/journey/VisitorSelector";
import { JourneyDetail } from "@/pages/journey/JourneyDetail";

export function JourneyPage() {
  const { anonymousId } = useParams();
  return anonymousId ? <JourneyDetail /> : <VisitorSelector />;
}
