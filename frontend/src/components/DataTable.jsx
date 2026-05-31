import React from 'react'

const DataTable = ({ 
  columns, 
  data = [], 
  isLoading = false, 
  onRowClick,
  emptyMessage = "No se encontraron registros."
}) => {

  return (
    <div className="overflow-x-auto w-full bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 rounded-xl shadow-premium">
      <table className="w-full text-left border-collapse">
        {/* Table Head */}
        <thead>
          <tr className="bg-slate-50 dark:bg-legal-charcoal-dark border-b border-slate-100 dark:border-slate-800">
            {columns.map((col, idx) => (
              <th 
                key={idx} 
                className="px-6 py-4 text-xs font-bold text-legal-navy-medium dark:text-slate-400 uppercase tracking-widest"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        
        {/* Table Body */}
        <tbody>
          {isLoading ? (
            // Skeleton loader representation
            Array.from({ length: 5 }).map((_, rIdx) => (
              <tr key={rIdx} className="border-b border-slate-100 dark:border-slate-800/50">
                {columns.map((_, cIdx) => (
                  <td key={cIdx} className="px-6 py-4.5">
                    <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3 animate-pulse"></div>
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td 
                colSpan={columns.length} 
                className="px-6 py-12 text-center text-slate-400 dark:text-slate-500 font-medium"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rIdx) => (
              <tr 
                key={row.id || rIdx} 
                onClick={() => onRowClick && onRowClick(row)}
                className={`border-b border-slate-100 dark:border-slate-800/50 transition-all duration-150 ${
                  onRowClick 
                    ? 'cursor-pointer hover:bg-slate-50/50 dark:hover:bg-slate-800/20' 
                    : ''
                }`}
              >
                {columns.map((col, cIdx) => (
                  <td 
                    key={cIdx} 
                    className="px-6 py-4 text-sm font-medium text-slate-700 dark:text-slate-200"
                  >
                    {col.render ? col.render(row) : row[col.accessor]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

export default DataTable
