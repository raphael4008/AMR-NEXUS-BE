import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  ClockIcon,
  BellIcon,
  Cog6ToothIcon,
  BeakerIcon,
  DocumentChartBarIcon,
  ArrowPathIcon,        
  MagnifyingGlassIcon,   
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Predict', href: '/predict', icon: BeakerIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'History', href: '/history', icon: ClockIcon },
  { name: 'Alerts', href: '/alerts', icon: BellIcon },
  { name: 'Reports', href: '/reports', icon: DocumentChartBarIcon },
  { name: 'Compare', href: '/compare', icon: ArrowPathIcon },           
  { name: 'Pathogen Explorer', href: '/pathogen-explorer', icon: MagnifyingGlassIcon }, 
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export default function Sidebar({ mobile = false, onNavigate }) {
  // Executive floating oval pill styling
  const linkClasses = ({ isActive }) =>
    `group flex items-center px-4 py-2.5 mx-2 my-1 text-sm font-medium rounded-full transition-all duration-200 ease-out ${
      isActive
        ? 'bg-white shadow-md ring-1 ring-primary-100/50 text-primary-700'
        : 'text-gray-600 hover:bg-white/60 hover:shadow-sm hover:text-gray-900'
    }`;

  const iconClasses = ({ isActive }) =>
    `mr-3 h-5 w-5 flex-shrink-0 transition-colors ${
      isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-gray-600'
    }`;

  const handleClick = () => {
    if (mobile && onNavigate) onNavigate();
  };

  return (
    <nav className="flex-1 space-y-0.5 px-2 py-4">
      {navigation.map((item) => (
        <NavLink
          key={item.name}
          to={item.href}
          className={linkClasses}
          onClick={handleClick}
          end={item.href === '/'}
        >
          {({ isActive }) => (
            <>
              <item.icon className={iconClasses({ isActive })} aria-hidden="true" />
              <span className="tracking-wide font-medium">{item.name}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}