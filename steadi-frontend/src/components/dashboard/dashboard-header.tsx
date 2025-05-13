import {Link} from "react-router-dom"
import { ModeToggle } from "@/components/dashboard/mode-toggle"
import { Button } from "@/components/ui/button"
import { Bell, HelpCircle, LogOut, Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/lib/AuthContext"
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

export function DashboardHeader() {
  const { signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
  };

  return (
    <header className=" px-4 sticky top-0 z-50 w-full border-b border-[#2a2a30] bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold steadi-gradient-text">Steadi.</span>
          </Link>
          <nav className="hidden md:flex gap-6">
            <Link to="#" className="text-sm font-medium transition-colors hover:text-primary relative group">
              Dashboard
              <span className="absolute -bottom-1 left-0 w-full h-[2px] bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></span>
            </Link>
            <Link
              to="#"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary relative group"
            >
              Suppliers
              <span className="absolute -bottom-1 left-0 w-full h-[2px] bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></span>
            </Link>
            <Link
              to="#"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary relative group"
            >
              Products
              <span className="absolute -bottom-1 left-0 w-full h-[2px] bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></span>
            </Link>
            <Link
              to="#"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary relative group"
            >
              Sales
              <span className="absolute -bottom-1 left-0 w-full h-[2px] bg-gradient-to-r from-steadi-red via-steadi-pink to-steadi-purple transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></span>
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden md:block">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search..."
              className="w-[200px] pl-8 md:w-[240px] lg:w-[320px] bg-muted/50 border-[#2a2a30] focus-visible:ring-steadi-pink"
            />
          </div>
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-steadi-red text-[10px] text-white">
              3
            </span>
          </Button>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-5 w-5" />
          </Button>
          <ModeToggle />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" onClick={handleLogout}>
                  <LogOut className="h-5 w-5 text-muted-foreground hover:text-foreground transition-colors" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Logout</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </header>
  )
}
