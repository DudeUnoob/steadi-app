import { Link } from 'react-router-dom'
import { IconInfoCircle, IconChartBar, IconBox, IconCash, IconTruckDelivery } from '@tabler/icons-react'

function Dashboard() {
  const links = [
    {
      label: "Dashboard",
      href: "/dashboard",
      icon: <IconChartBar className="text-black" size={20} />
    },
    {
      label: "Sales",
      href: "#sales",
      icon: <IconCash className="text-black" size={20} />
    },
    {
      label: "Products",
      href: "#products",
      icon: <IconBox className="text-black" size={20} />
    },
    {
      label: "Inventory",
      href: "#inventory",
      icon: <IconBox className="text-black" size={20} />
    },
    {
      label: "Suppliers",
      href: "#suppliers",
      icon: <IconTruckDelivery className="text-black" size={20} />
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex">
      {/* Custom Sidebar */}
      <div className="fixed left-0 top-0 bottom-0 w-64 bg-[#ff5757]/70 h-full shadow-xl z-10">
        <div className="p-6">
          <Link to="/" className="text-3xl font-light text-black font-['Poppins']">Steadi.</Link>
        </div>
        <div className="flex flex-col gap-4 mt-10 px-6">
          {links.map((link) => (
            <a 
              key={link.label} 
              href={link.href} 
              className="flex items-center gap-3 text-black hover:translate-x-1 transition-transform"
            >
              <span>{link.icon}</span>
              <span className="font-['Poppins']">{link.label}</span>
            </a>
          ))}
        </div>
      </div>

      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="px-6 py-4 flex justify-between items-center">
          <div className="flex-1"></div>
          <div className="flex space-x-10">
            <a href="#features" className="text-black font-['Poppins'] font-medium">Features</a>
            <a href="#solutions" className="text-black font-['Poppins'] font-medium">Solutions</a>
            <a href="#about" className="text-black font-['Poppins'] font-medium">About</a>
          </div>
          <div>
            <span className="bg-black text-white px-6 py-3 rounded-full font-['Poppins'] font-medium">
              Dashboard
            </span>
          </div>
        </header>

        {/* Main Dashboard Grid */}
        <div className="p-10 grid grid-cols-2 gap-6">
          {/* First row, first column */}
          <div className="border border-black/20 rounded-lg p-6 h-64 backdrop-blur-sm bg-white/5 relative">
            <div className="absolute top-6 left-6">
              <IconInfoCircle size={24} className="text-black" />
            </div>
            <h2 className="text-2xl font-['Poppins'] font-medium text-black ml-10">Sales</h2>
          </div>
          
          {/* First row, second column */}
          <div className="border border-black/20 rounded-lg p-6 h-64 backdrop-blur-sm bg-white/5 relative">
            <div className="absolute top-6 left-6">
              <IconInfoCircle size={24} className="text-black" />
            </div>
            <h2 className="text-2xl font-['Poppins'] font-medium text-black ml-10">Products</h2>
          </div>
          
          {/* Second row, first column */}
          <div className="border border-black/20 rounded-lg p-6 h-64 backdrop-blur-sm bg-white/5 relative">
            <div className="absolute top-6 left-6">
              <IconInfoCircle size={24} className="text-black" />
            </div>
            <h2 className="text-2xl font-['Poppins'] font-medium text-black ml-10">Inventory</h2>
          </div>
          
          {/* Second row, second column */}
          <div className="border border-black/20 rounded-lg p-6 h-64 backdrop-blur-sm bg-white/5 relative">
            <div className="absolute top-6 left-6">
              <IconInfoCircle size={24} className="text-black" />
            </div>
            <h2 className="text-2xl font-['Poppins'] font-medium text-black ml-10">Suppliers</h2>
          </div>
          
          {/* Third row spanning both columns */}
          <div className="border border-blue-500 border-black/20 rounded-lg p-6 col-span-2 min-h-[350px] backdrop-blur-sm bg-white/5 relative">
            <div className="absolute top-6 left-6">
              <IconInfoCircle size={24} className="text-black" />
            </div>
            <h2 className="text-2xl font-['Poppins'] font-medium text-black ml-10">
              <span className="underline">Sales Graph</span>
            </h2>
            
            {/* Simple chart */}
            <div className="mt-10 h-64 w-full">
              <div className="w-full h-full flex items-end justify-around">
                {[40, 70, 50, 90, 60, 80, 75, 95, 45, 65, 85, 55].map((height, idx) => (
                  <div key={idx} className="h-full flex items-end">
                    <div 
                      className="w-8 bg-black/20 rounded-t-sm"
                      style={{ height: `${height}%` }}
                    ></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard 