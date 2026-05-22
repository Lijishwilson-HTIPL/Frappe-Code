// Place this file in your Next.js project: src/services/careerInquiry.ts

export interface CareerInquiryPayload {
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  role_applying_for: string;
  years_of_experience: number;
  linkedin_profile_url: string;
  tell_us_about_yourself: string;
  resume_link?: string;
  portfolio_site?: string;
  how_did_you_hear?: string;
}

export interface CareerInquiryResponse {
  status: "success";
  name: string;
}

declare const process: { env: Record<string, string | undefined> };

const ERPNEXT_URL =
  process.env.NEXT_PUBLIC_ERPNEXT_URL ?? "http://mysite.local:8001";

const API_METHOD =
  "erpnext.setup.doctype.career_inquiry.career_inquiry.submit_career_inquiry";

export async function submitCareerInquiry(
  payload: CareerInquiryPayload
): Promise<CareerInquiryResponse> {
  const params = new URLSearchParams();

  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      params.append(key, String(value));
    }
  });

  const res = await fetch(`${ERPNEXT_URL}/api/method/${API_METHOD}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params.toString(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.exception ?? "Failed to submit application");
  }

  const data = await res.json();
  return data.message as CareerInquiryResponse;
}
