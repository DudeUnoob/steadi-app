"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/components/ui/use-toast"
import { Shield, Users, Building } from "lucide-react"
import { useAuth, UserRole } from "@/lib/AuthContext"
import { supabase } from "@/lib/supabase"

const RoleCard = ({ 
  title, 
  description, 
  icon, 
  onClick, 
  isSelected 
}: { 
  title: string; 
  description: string; 
  icon: React.ReactNode; 
  onClick: () => void; 
  isSelected: boolean;
}) => (
  <div 
    onClick={onClick}
    className={`relative cursor-pointer rounded-lg border p-4 transition-all hover:shadow-md ${
      isSelected 
        ? "border-steadi-pink bg-black/40" 
        : "border-[#2a2a30] bg-black/20 hover:border-steadi-pink/50"
    }`}
  >
    <div className="flex items-start gap-3">
      <div className="mt-0.5 text-steadi-pink">
        {icon}
      </div>
      <div>
        <h3 className="font-medium text-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
    {isSelected && (
      <div className="absolute -right-1.5 -top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-steadi-pink text-[10px] font-medium text-white">
        ✓
      </div>
    )}
  </div>
)

export default function RoleSelectionPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [selectedRole, setSelectedRole] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { user } = useAuth()

  const handleContinue = async () => {
    if (!selectedRole) {
      toast({
        title: "Please select a role",
        description: "Select your role in the organization to continue.",
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)

    try {
      // Update user metadata with the selected role
      const { error } = await supabase.auth.updateUser({
        data: { role: selectedRole }
      })

      if (error) {
        throw new Error(error.message)
      }

      // Set appropriate localStorage flags based on role
      if (selectedRole === UserRole.OWNER) {
        // Owner needs to set up rules
        localStorage.setItem('rules_setup_required', 'true')
        localStorage.setItem('rules_setup_completed', 'false')
        localStorage.setItem('org_code_required', 'false')
        // Clear any existing organization ID since owner will create a new one
        localStorage.removeItem('organization_id')
        navigate("/auth/rules")
      } else {
        // Staff and Manager need to enter organization code
        localStorage.setItem('rules_setup_required', 'false')
        localStorage.setItem('org_code_required', 'true')
        navigate("/auth/organization")
      }

    } catch (error) {
      console.error("Error setting user role:", error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to set your role. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center bg-background p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-steadi-red/10 blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 h-[600px] w-[600px] rounded-full bg-steadi-purple/10 blur-[100px]" />
        <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-steadi-pink/10 blur-[100px]" />
        <div className="absolute inset-0 grid-pattern opacity-20" />
      </div>

      <div className="z-10 w-full max-w-md">
        <div className="flex flex-col items-center space-y-2 text-center">
          <span className="text-3xl font-bold steadi-gradient-text">Steadi.</span>
          <h1 className="text-2xl font-bold tracking-tight">Select Your Role</h1>
          <p className="text-sm text-muted-foreground">Choose your role to complete the sign-up process</p>
        </div>

        <Card className="mt-8 overflow-hidden border-0 bg-black/40 backdrop-blur-xl">
          <CardHeader>
            <CardTitle>Your Role</CardTitle>
            <CardDescription>Select your role in the organization</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <RoleCard
              title="Owner"
              description="I'm creating a new organization and will manage all aspects of it."
              icon={<Shield className="h-5 w-5" />}
              onClick={() => setSelectedRole(UserRole.OWNER)}
              isSelected={selectedRole === UserRole.OWNER}
            />
            <RoleCard
              title="Manager"
              description="I have elevated permissions but am joining an existing organization."
              icon={<Building className="h-5 w-5" />}
              onClick={() => setSelectedRole(UserRole.MANAGER)}
              isSelected={selectedRole === UserRole.MANAGER}
            />
            <RoleCard
              title="Staff"
              description="I'm a team member joining an existing organization."
              icon={<Users className="h-5 w-5" />}
              onClick={() => setSelectedRole(UserRole.STAFF)}
              isSelected={selectedRole === UserRole.STAFF}
            />
          </CardContent>
          <CardFooter className="flex justify-end border-t border-[#2a2a30] bg-muted/10 px-6 py-4">
            <Button
              onClick={handleContinue}
              className="bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple hover:opacity-90"
              disabled={isSubmitting || !selectedRole}
            >
              {isSubmitting ? "Processing..." : "Continue"}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
} 