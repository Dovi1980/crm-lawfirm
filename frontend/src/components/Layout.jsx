import React from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Navbar from './Navbar'

const Layout = () => {
  return (
    <div className="min-h-screen flex bg-legal-cream dark:bg-legal-charcoal-dark transition-colors duration-200">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Layout Container */}
      <div className="flex-1 flex flex-col pl-64">
        {/* Top Navbar Header */}
        <Navbar />

        {/* Scrollable Worksite Content Area */}
        <main className="flex-grow pt-16 p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
