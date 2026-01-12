import { Fragment } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { Check, ChevronDown } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
}

export const Select = ({
  value,
  onChange,
  options,
  placeholder = '请选择',
  className = '',
}: SelectProps) => {
  const selectedOption = options.find(opt => opt.value === value);
  
  return (
    <Listbox value={value} onChange={onChange}>
      {({ open }) => (
        <div className={`relative ${className}`}>
          <Listbox.Button className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-medium text-slate-700 outline-none hover:border-indigo-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10 transition-all shadow-sm hover:shadow-md cursor-pointer text-left flex items-center justify-between">
            <span className={selectedOption && value ? 'text-slate-700 font-bold' : 'text-slate-400'}>
              {selectedOption?.label || placeholder}
            </span>
            <ChevronDown 
              size={16} 
              className={`text-slate-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
            />
          </Listbox.Button>
          
          <Transition
            as={Fragment}
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <Listbox.Options className="absolute mt-2 w-full bg-white border border-slate-100 rounded-2xl shadow-2xl py-2 z-50 max-h-60 overflow-auto focus:outline-none custom-scrollbar">
              {options.map((option) => (
                <Listbox.Option
                  key={option.value}
                  value={option.value}
                  disabled={option.value === ''}
                  className={({ active, disabled }) =>
                    `relative cursor-pointer select-none py-3 px-4 transition-colors ${
                      disabled ? 'opacity-50 cursor-not-allowed' : ''
                    } ${
                      active && !disabled ? 'bg-indigo-50 text-indigo-600' : 'text-slate-700'
                    }`
                  }
                >
                  {({ selected, active }) => (
                    <div className="flex items-center justify-between">
                      <span className={`block truncate ${selected ? 'font-bold' : 'font-medium'}`}>
                        {option.label}
                      </span>
                      {selected && option.value && (
                        <Check 
                          size={16} 
                          className={`${active ? 'text-indigo-600' : 'text-indigo-500'}`}
                        />
                      )}
                    </div>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </Transition>
        </div>
      )}
    </Listbox>
  );
};
