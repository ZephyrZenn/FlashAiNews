import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

interface DropDownItemProps {
  children: React.ReactNode;
  onClick: () => void;
}

interface DropDownMenuProps {
  trigger: React.ReactNode;
  items: DropDownItemProps[];
}

export const DropDownMenu = ({ trigger, items }: DropDownMenuProps) => {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>{trigger}</DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content className="bg-white rounded-md shadow-md p-2 border">
          {items.map((item, index) => (
            <DropdownMenu.Item
              key={index}
              onClick={item.onClick}
              className="px-3 py-2 hover:bg-gray-100 cursor-pointer rounded text-sm"
            >
              {item.children}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
};
