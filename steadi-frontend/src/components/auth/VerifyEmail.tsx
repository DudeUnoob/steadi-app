import { ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function VerifyEmail() {
  const navigate = useNavigate();

  const handleBackToLogin = () => {
    navigate("/auth");
  };

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center bg-background p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-steadi-red/10 blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 h-[600px] w-[600px] rounded-full bg-steadi-purple/10 blur-[100px]" />
        <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-steadi-pink/10 blur-[100px]" />
        <div className="absolute inset-0 grid-pattern opacity-20" />
      </div>

      <div className="z-10 w-full max-w-md">
        <div className="flex flex-col items-center space-y-4 text-center">
          <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-steadi-red via-steadi-pink to-steadi-purple p-[1px]">
            <div className="flex h-full w-full items-center justify-center rounded-full bg-black">
              <ShieldCheck className="h-8 w-8 text-white" />
            </div>
          </div>
          <span className="text-3xl font-bold steadi-gradient-text">Steadi.</span>
          
          <div className="bg-black/40 backdrop-blur-xl rounded-lg border border-[#2a2a30] p-8 w-full">
            <h1 className="text-2xl font-bold mb-2">Check Your Email</h1>
            <p className="text-sm text-muted-foreground mb-6">
              We've sent a verification link to your email address.
              Please check your inbox and click the link to verify your account.
            </p>

            <div className="space-y-4">
              <div className="p-4 rounded-md bg-steadi-pink/10 border border-steadi-pink/20">
                <p className="text-sm">
                  Once verified, you'll be automatically redirected to set up your organization roles.
                </p>
              </div>

              <Button
                variant="outline"
                className="w-full border-[#2a2a30] bg-transparent hover:bg-muted/20"
                onClick={handleBackToLogin}
              >
                Back to Login
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 